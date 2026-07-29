"""Core crawl4ai async-to-sync bridge.

Provides synchronous wrapper functions for use in Huey task threads.
Manages the Playwright browser lifecycle per-crawl invocation.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

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
    cancel_checker: Optional[Callable[[], bool]] = None,
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
        cancel_checker: Optional callback returning True to abort mid-crawl.

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
        cancel_checker=cancel_checker,
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
    cancel_checker: Optional[Callable[[], bool]] = None,
) -> CrawlResult:
    """Crawl a URL and return both markdown and HTML content.

    Args:
        url: Target URL.
        wait_for: Optional CSS selector to wait for before extracting.
        css_selector: Optional CSS selector to restrict extraction scope.
        timeout: Page load timeout in milliseconds.
        js_code: Optional JavaScript to execute before extraction.
        auto_tab_click: If True, automatically click tab elements.
        cancel_checker: Optional callback returning True to abort mid-crawl.
            When set, the crawl races against a cancel watcher; on cancel the
            Playwright browser is closed immediately instead of waiting for
            the page load / tab-click sequence to finish.

    Returns:
        CrawlResult with markdown, html, and success flag.
        On cancellation, returns an empty unsuccessful CrawlResult.
    """
    if cancel_checker is not None and cancel_checker():
        return CrawlResult()

    return asyncio.run(
        _async_crawl(
            url,
            wait_for=wait_for,
            css_selector=css_selector,
            timeout=timeout,
            js_code=js_code,
            auto_tab_click=auto_tab_click,
            cancel_checker=cancel_checker,
        )
    )


class CrawlCancelled(Exception):
    """Raised internally when cancel_checker fires during an async crawl."""


async def _async_crawl(
    url: str,
    *,
    wait_for: Optional[str] = None,
    css_selector: Optional[str] = None,
    timeout: int = 60000,
    js_code: Optional[str] = None,
    auto_tab_click: bool = False,
    max_retries: int = 1,
    cancel_checker: Optional[Callable[[], bool]] = None,
) -> CrawlResult:
    """Async implementation of URL crawling using crawl4ai.

    Args:
        url: Target URL.
        wait_for: Optional CSS selector to wait for before extracting.
        css_selector: Optional CSS selector to restrict extraction scope.
        timeout: Page load timeout in milliseconds.
        js_code: Optional JavaScript to execute before extraction.
        auto_tab_click: If True, automatically click tab elements.
        max_retries: Number of retries on connection errors (default 1).
        cancel_checker: Optional callback returning True to abort.

    Returns:
        CrawlResult with markdown, html, and success flag.
    """
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

    last_error: Optional[str] = None
    for attempt in range(max_retries + 1):
        if cancel_checker is not None and cancel_checker():
            await _cleanup_crawler()
            return CrawlResult()

        crawl_task = asyncio.create_task(
            _run_single_crawl(url, run_config)
        )
        cancel_task: Optional[asyncio.Task] = None
        if cancel_checker is not None:
            cancel_task = asyncio.create_task(_watch_cancel(cancel_checker))

        try:
            if cancel_task is None:
                result, error = await crawl_task
            else:
                done, pending = await asyncio.wait(
                    {crawl_task, cancel_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if cancel_task in done:
                    for t in pending:
                        t.cancel()
                    await _cleanup_crawler()
                    return CrawlResult()
                for t in pending:
                    t.cancel()
                result, error = crawl_task.result()
        except CrawlCancelled:
            await _cleanup_crawler()
            return CrawlResult()
        except Exception as e:
            last_error = str(e)
            await _cleanup_crawler()
            if _is_connection_error(last_error) and attempt < max_retries:
                logger.warning(
                    "crawl4ai connection error for %s (attempt %d/%d), will retry...",
                    url, attempt + 1, max_retries + 1,
                )
                await asyncio.sleep(1.0)
                continue
            logger.exception("crawl4ai error for %s", url)
            return CrawlResult()

        if error is not None:
            last_error = error
            await _cleanup_crawler()
            if _is_connection_error(last_error) and attempt < max_retries:
                logger.warning(
                    "crawl4ai connection error for %s (attempt %d/%d), will retry...",
                    url, attempt + 1, max_retries + 1,
                )
                await asyncio.sleep(1.0)
                continue
            logger.exception("crawl4ai error for %s", url)
            return CrawlResult()

        if result and result.success:
            await _cleanup_crawler()
            return CrawlResult(
                markdown=result.markdown or "",
                html=result.cleaned_html or result.html or "",
                success=True,
            )

        last_error = str(getattr(result, "error_message", "unknown"))
        await _cleanup_crawler()
        if _is_connection_error(last_error) and attempt < max_retries:
            logger.warning(
                "crawl4ai connection error for %s (attempt %d/%d), will retry...",
                url, attempt + 1, max_retries + 1,
            )
            await asyncio.sleep(1.0)
            continue
        logger.warning("crawl4ai failed for %s: %s", url, last_error)
        return CrawlResult()

    logger.warning("crawl4ai failed for %s after %d retries: %s", url, max_retries, last_error)
    return CrawlResult()


async def _run_single_crawl(url: str, run_config) -> tuple:
    """Run one crawl attempt; returns (result, error_str_or_None)."""
    try:
        crawler = await _get_or_create_crawler()
        result = await crawler.arun(url=url, config=run_config)
        return result, None
    except Exception as e:
        return None, str(e)


async def _watch_cancel(cancel_checker: Callable[[], bool]) -> None:
    """Poll cancel_checker until it returns True, then raise CrawlCancelled."""
    while True:
        if cancel_checker():
            raise CrawlCancelled()
        await asyncio.sleep(0.25)


def _is_connection_error(error_msg: str) -> bool:
    """Check if error message indicates a connection-related error.

    These errors might be transient and benefit from a retry with a fresh
    browser instance.
    """
    connection_error_patterns = [
        "ERR_CONNECTION_CLOSED",
        "ERR_CONNECTION_RESET",
        "ERR_CONNECTION_REFUSED",
        "ERR_NAME_NOT_RESOLVED",
        "ERR_NETWORK_CHANGED",
        "ERR_INTERNET_DISCONNECTED",
        "net::ERR",
        "Failed on navigating",
        "page.goto",
        "Navigation failed",
        "Target page, context or browser has been closed",
        "Browser has been closed",
        "Protocol error",
    ]
    error_lower = error_msg.lower()
    return any(pattern.lower() in error_lower for pattern in connection_error_patterns)
