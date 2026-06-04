"""Core crawl4ai async-to-sync bridge.

Provides synchronous wrapper functions for use in Huey task threads.
Manages the Playwright browser lifecycle per-crawl invocation.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result from a crawl operation, containing both markdown and HTML."""

    markdown: str = ""
    html: str = ""
    success: bool = False


# JavaScript code that clicks through common tab/navigation elements
# to trigger AJAX content loading on Chinese university pages.
# NOTE: no `break` — we click ALL matching groups so that pages with
# multiple tab layers (e.g. category tabs + title tabs) get fully loaded.
_TAB_CLICK_JS = """
await new Promise(r => setTimeout(r, 3000));
const tabSelectors = [
    '.gg li', '.zc li', '.tab-nav li', '.tabs li',
    '.wp_column_nav li', '.nav-tabs li', '.category li',
    '[role="tab"]', '.tab-item', '.filter-item'
];
for (const sel of tabSelectors) {
    const tabs = document.querySelectorAll(sel);
    if (tabs.length > 0) {
        for (let tab of tabs) {
            tab.click();
            if (window.jQuery) { jQuery(tab).trigger('click'); }
            await new Promise(r => setTimeout(r, 1000));
        }
        await new Promise(r => setTimeout(r, 2000));
    }
}
"""

# Thread-local storage for per-thread browser instance reuse.
# Each Huey worker thread gets its own Playwright browser that persists
# across multiple crawl_url_full calls, avoiding the ~2s startup cost
# per invocation.
_thread_local = threading.local()


def _get_cached_crawler():
    """Return a cached AsyncWebCrawler for the current thread, or None."""
    return getattr(_thread_local, "crawler", None)


def _set_cached_crawler(crawler) -> None:
    """Cache an AsyncWebCrawler for the current thread."""
    _thread_local.crawler = crawler


def _clear_cached_crawler() -> None:
    """Clear the cached crawler for the current thread."""
    _thread_local.crawler = None


async def _get_or_create_crawler():
    """Get the cached AsyncWebCrawler or create a new one.

    The crawler is cached per-thread so that pagination-heavy crawls
    (CSS mode) reuse the same browser instance instead of paying the
    Playwright startup cost on every page.
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig

    cached = _get_cached_crawler()
    if cached is not None:
        return cached

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    _set_cached_crawler(crawler)
    return crawler


async def _cleanup_crawler() -> None:
    """Clean up the cached browser for the current thread."""
    cached = _get_cached_crawler()
    if cached is not None:
        try:
            await cached.__aexit__(None, None, None)
        except Exception:
            pass
        _clear_cached_crawler()


def crawl_url(
    url: str,
    *,
    wait_for: Optional[str] = None,
    css_selector: Optional[str] = None,
    timeout: int = 60000,
    js_code: Optional[str] = None,
    auto_tab_click: bool = False,
) -> str:
    """Crawl a URL and return its markdown content.

    Args:
        url: Target URL.
        wait_for: Optional CSS selector to wait for before extracting.
        css_selector: Optional CSS selector to restrict extraction scope.
        timeout: Page load timeout in milliseconds.
        js_code: Optional JavaScript to execute before extraction.
        auto_tab_click: If True, automatically click tab elements to
            trigger AJAX content loading (useful for Chinese university sites).

    Returns:
        Markdown string of the page content.  Empty string on failure.
    """
    result = crawl_url_full(
        url,
        wait_for=wait_for,
        css_selector=css_selector,
        timeout=timeout,
        js_code=js_code,
        auto_tab_click=auto_tab_click,
    )
    return result.markdown


def crawl_url_full(
    url: str,
    *,
    wait_for: Optional[str] = None,
    css_selector: Optional[str] = None,
    timeout: int = 60000,
    js_code: Optional[str] = None,
    auto_tab_click: bool = False,
) -> CrawlResult:
    """Crawl a URL and return both markdown and HTML content.

    Args:
        url: Target URL.
        wait_for: Optional CSS selector to wait for before extracting.
        css_selector: Optional CSS selector to restrict extraction scope.
        timeout: Page load timeout in milliseconds.
        js_code: Optional JavaScript to execute before extraction.
        auto_tab_click: If True, automatically click tab elements.

    Returns:
        CrawlResult with markdown, html, and success flag.
    """
    return asyncio.run(
        _async_crawl(
            url,
            wait_for=wait_for,
            css_selector=css_selector,
            timeout=timeout,
            js_code=js_code,
            auto_tab_click=auto_tab_click,
        )
    )


async def _async_crawl(
    url: str,
    *,
    wait_for: Optional[str] = None,
    css_selector: Optional[str] = None,
    timeout: int = 60000,
    js_code: Optional[str] = None,
    auto_tab_click: bool = False,
) -> CrawlResult:
    """Async implementation of URL crawling using crawl4ai."""
    try:
        from crawl4ai import CrawlerRunConfig
    except ImportError:
        logger.warning("crawl4ai not installed, falling back to empty result")
        return CrawlResult()

    # Combine auto_tab_click with custom js_code
    combined_js = ""
    if auto_tab_click:
        combined_js = _TAB_CLICK_JS
    if js_code:
        combined_js = combined_js + "\n" + js_code if combined_js else js_code

    run_kwargs: dict = {
        "page_timeout": timeout,
        "wait_until": "networkidle",
        "delay_before_return_html": 2.0,
    }

    if css_selector:
        run_kwargs["css_selector"] = css_selector

    if wait_for:
        run_kwargs["wait_for"] = wait_for

    if combined_js:
        run_kwargs["js_code"] = combined_js

    run_config = CrawlerRunConfig(**run_kwargs)

    try:
        # Reuse the per-thread browser if available; otherwise create a new one.
        crawler = await _get_or_create_crawler()
        try:
            result = await crawler.arun(url=url, config=run_config)
            if result and result.success:
                return CrawlResult(
                    markdown=result.markdown or "",
                    html=result.cleaned_html or result.html or "",
                    success=True,
                )
            logger.warning("crawl4ai failed for %s: %s", url, getattr(result, "error_message", "unknown"))
            return CrawlResult()
        finally:
            # Always clean up the browser after this event loop finishes,
            # since asyncio.run() creates a new loop each time.
            await _cleanup_crawler()
    except Exception:
        logger.exception("crawl4ai error for %s", url)
        return CrawlResult()
