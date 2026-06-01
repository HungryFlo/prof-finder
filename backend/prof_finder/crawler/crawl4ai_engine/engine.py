"""Core crawl4ai async-to-sync bridge.

Provides synchronous wrapper functions for use in Huey task threads.
Manages the Playwright browser lifecycle per-crawl invocation.
"""

from __future__ import annotations

import asyncio
import logging
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
        break;
    }
}
"""


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
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    except ImportError:
        logger.warning("crawl4ai not installed, falling back to empty result")
        return CrawlResult()

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )

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
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            if result and result.success:
                return CrawlResult(
                    markdown=result.markdown or "",
                    html=result.cleaned_html or result.html or "",
                    success=True,
                )
            logger.warning("crawl4ai failed for %s: %s", url, getattr(result, "error_message", "unknown"))
            return CrawlResult()
    except Exception:
        logger.exception("crawl4ai error for %s", url)
        return CrawlResult()
