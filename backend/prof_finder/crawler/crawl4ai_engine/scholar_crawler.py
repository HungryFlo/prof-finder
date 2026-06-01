"""crawl4ai-based Google Scholar crawler.

This module provides a fallback for the scholarly-based ScholarCrawler.
It uses crawl4ai's Playwright-based browser to fetch Google Scholar pages,
which is more resilient to anti-bot blocking.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

from .engine import crawl_url

logger = logging.getLogger(__name__)

_SCHOLAR_BASE = "https://scholar.google.com"


class Crawl4AIScholarCrawler:
    """Google Scholar crawler using crawl4ai for more reliable scraping."""

    def get_author(self, scholar_id: str) -> Optional[dict]:
        """Fetch author profile and publications from Google Scholar.

        Args:
            scholar_id: Google Scholar user ID.

        Returns:
            Dict with author data matching ScholarCrawler.get_author format,
            or None if not found.
        """
        url = (
            f"{_SCHOLAR_BASE}/citations?user={scholar_id}"
            "&cstart=0&pagesize=100&sortby=pubdate"
        )

        try:
            html = self._fetch_scholar_html(url)
            if not html:
                return None
            return self._parse_author_page(html, scholar_id)
        except Exception:
            logger.exception("crawl4ai scholar get_author failed for %s", scholar_id)
            return None

    def search_author(self, query: str, limit: int = 10) -> list[dict]:
        """Search Google Scholar for authors.

        Args:
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            List of dicts with keys: name, affiliation, scholar_id, interests, citedby.
        """
        from urllib.parse import quote

        url = f"{_SCHOLAR_BASE}/scholar?q={quote(query)}&view_op=search_authors"

        try:
            html = self._fetch_scholar_html(url)
            if not html:
                return []
            return self._parse_search_results(html, limit)
        except Exception:
            logger.exception("crawl4ai scholar search_author failed for %s", query)
            return []

    def fill_publication(self, author_pub_id: str) -> dict:
        """Fetch full publication details (abstract, links, etc.).

        Args:
            author_pub_id: Publication ID in format ``{author_id}_{pub_id}``.

        Returns:
            Dict with publication details (abstract, links, etc.).
        """
        url = (
            f"{_SCHOLAR_BASE}/citations"
            f"?view_op=view_citation&citation_for_view={author_pub_id}"
        )

        try:
            html = self._fetch_scholar_html(url)
            if not html:
                return {}
            return self._parse_publication_page(html)
        except Exception:
            logger.exception("crawl4ai fill_publication failed for %s", author_pub_id)
            return {}

    # ---- Internal helpers ----

    def _fetch_scholar_html(self, url: str) -> str:
        """Fetch Google Scholar page HTML via crawl4ai, with fallback to requests."""
        try:
            import asyncio
            html = asyncio.run(self._async_fetch(url))
            if html:
                return html
        except Exception:
            logger.debug("crawl4ai fetch failed, trying requests fallback")

        # Fallback to requests with a simple user-agent
        try:
            import requests
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            })
            resp.raise_for_status()
            return resp.text
        except Exception:
            logger.exception("Both crawl4ai and requests failed for %s", url)
            return ""

    async def _async_fetch(self, url: str) -> str:
        """Async fetch using crawl4ai."""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        except ImportError:
            return ""

        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )
        run_config = CrawlerRunConfig(
            page_timeout=30000,
            wait_for="table#gsc_a_b",  # Wait for publications table
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            if result and result.success:
                return result.html or ""
            return ""

    def _parse_author_page(self, html: str, scholar_id: str) -> Optional[dict]:
        """Parse Google Scholar author profile page."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        # Extract name
        name_el = soup.select_one("#gsc_prf_in")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        # Extract affiliation
        affiliation_el = soup.select_one("#gsc_prf_in+div")
        affiliation = affiliation_el.get_text(strip=True) if affiliation_el else ""

        # Extract research interests
        interests: list[str] = []
        interest_els = soup.select("#gsc_prf_int a")
        for el in interest_els:
            text = el.get_text(strip=True)
            if text:
                interests.append(text)

        # Extract stats (h-index, citations)
        h_index = None
        citations = None
        stats_els = soup.select("#gsc_rsb_st td.gsc_rsb_std")
        if len(stats_els) >= 2:
            try:
                citations = int(stats_els[0].get_text(strip=True))
            except ValueError:
                pass
        if len(stats_els) >= 5:
            try:
                h_index = int(stats_els[3].get_text(strip=True))
            except ValueError:
                pass

        # Extract publications
        publications: list[dict] = []
        pub_rows = soup.select("tr.gsc_a_tr")
        for row in pub_rows:
            pub = self._parse_publication_row(row)
            if pub:
                publications.append(pub)

        # Extract homepage
        homepage = None
        homepage_el = soup.select_one("#gsc_prf_ivh a")
        if homepage_el:
            homepage = homepage_el.get("href", "")

        return {
            "name": name,
            "affiliation": affiliation,
            "scholar_id": scholar_id,
            "interests": interests,
            "publications": publications,
            "h_index": h_index,
            "citations": citations,
            "homepage": homepage,
            "email": None,
        }

    def _parse_publication_row(self, row) -> Optional[dict]:
        """Parse a publication row from the author page."""
        title_el = row.select_one("a.gsc_a_at")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)

        # Extract author_pub_id from link
        author_pub_id = None
        href = title_el.get("href", "")
        if href:
            match = re.search(r"citation_for_view=([^&]+)", str(href))
            if match:
                author_pub_id = match.group(1)

        # Extract authors, venue, year
        details_els = row.select("div.gs_gray")
        authors = details_els[0].get_text(strip=True) if len(details_els) >= 1 else ""
        venue_text = details_els[1].get_text(strip=True) if len(details_els) >= 2 else ""

        # Parse year and venue from venue_text
        year = None
        venue = venue_text
        year_match = re.search(r"\b(19|20)\d{2}\b", venue_text)
        if year_match:
            year = int(year_match.group(0))
            venue = venue_text[: year_match.start()].strip().rstrip(",").strip()

        # Extract citations
        citations_el = row.select_one("a.gsc_a_c span")
        citations = None
        if citations_el:
            try:
                citations = int(citations_el.get_text(strip=True))
            except ValueError:
                pass

        return {
            "title": title,
            "authors": authors,
            "venue": venue,
            "year": year,
            "citations": citations,
            "author_pub_id": author_pub_id,
            "abstract": None,
            "links": [],
        }

    def _parse_search_results(self, html: str, limit: int) -> list[dict]:
        """Parse Google Scholar author search results."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []

        items = soup.select(".gs_ai_chpr")
        for item in items[:limit]:
            name_el = item.select_one(".gs_ai_name a")
            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            href = name_el.get("href", "")
            scholar_id = ""
            if "user=" in str(href):
                match = re.search(r"user=([a-zA-Z0-9_-]+)", str(href))
                if match:
                    scholar_id = match.group(1)

            affiliation_el = item.select_one(".gs_ai_aff")
            affiliation = affiliation_el.get_text(strip=True) if affiliation_el else ""

            interests_el = item.select_one(".gs_ai_int")
            interests: list[str] = []
            if interests_el:
                for a in interests_el.select("a"):
                    text = a.get_text(strip=True)
                    if text:
                        interests.append(text)

            cited_el = item.select_one(".gs_ai_cby")
            citedby = None
            if cited_el:
                text = cited_el.get_text(strip=True)
                match = re.search(r"(\d+)", text)
                if match:
                    citedby = int(match.group(1))

            results.append({
                "name": name,
                "affiliation": affiliation,
                "scholar_id": scholar_id,
                "interests": interests,
                "citedby": citedby,
            })

        return results

    def _parse_publication_page(self, html: str) -> dict:
        """Parse a publication detail page for abstract and links."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        result: dict = {}

        # Extract abstract
        abstract_el = soup.select_one("#gsc_oci_descr")
        if abstract_el:
            result["abstract"] = abstract_el.get_text(strip=True)

        # Extract external links
        links: list[dict] = []
        link_els = soup.select("#gsc_oci_table a.gsc_oci_title_link")
        for link_el in link_els:
            href = link_el.get("href", "")
            if href:
                links.append({"label": "link", "url": str(href)})
        if links:
            result["links"] = links

        return result
