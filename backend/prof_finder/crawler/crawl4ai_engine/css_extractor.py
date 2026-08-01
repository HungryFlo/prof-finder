"""CSS selector-based professor extraction using crawl4ai + BeautifulSoup.

Given a page URL and a dict of CSS selectors, extracts structured professor
data.  Supports pagination via a ``pagination_next`` selector, and AJAX-based
content loading via an ``ajax`` config block.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_professors_css(
    url: str,
    selectors: dict,
    affiliation: str = "",
    *,
    delay: float = 2.0,
    send_progress: Optional[Callable[[str], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
) -> list[dict]:
    """Extract professors from one or more pages using CSS selectors.

    Args:
        url: Starting page URL (professor list page).
        selectors: Dict mapping field names to CSS selectors.
            Required keys:
                name — selector for professor name element (text content)
            Optional keys:
                card — selector for each professor card/container
                profile_url — selector for link to profile page (href attr)
                title — selector for academic title (text content)
                email — selector for email element (text or mailto: href)
                research_interests — selector for interests (text content)
                photo_url — selector for photo (src attr)
                pagination_next — selector for "next page" link (href attr)
                max_pages — int, max pages to crawl (default 10)
                ajax — dict with AJAX config:
                    url — AJAX endpoint URL (absolute or relative to page URL)
                    method — HTTP method (default "POST")
                    params — dict of POST/GET parameters
                    response_field — JSON field containing HTML content (default "content")
        affiliation: Affiliation string to assign to all results.
        delay: Seconds to wait between page fetches.
        send_progress: Optional callback for progress messages.
        cancel_checker: Optional callback that returns True to abort.

    Returns:
        List of professor dicts with keys: name, url, title, email,
        photo_url, research_interests, affiliation.
    """
    results: list[dict] = []
    seen_names: set[str] = set()

    # Check if AJAX mode is configured
    ajax_config = selectors.get("ajax")
    if ajax_config:
        html = _fetch_ajax_content(url, ajax_config)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            page_profs = _extract_from_page(soup, selectors, affiliation, url)
            for prof in page_profs:
                name_key = prof["name"].strip().lower()
                if name_key and name_key not in seen_names:
                    seen_names.add(name_key)
                    results.append(prof)
        return results

    # Standard mode: crawl pages with CSS selectors
    current_url: str = url
    max_pages: int = int(selectors.get("max_pages", 10))

    for page_num in range(1, max_pages + 1):
        if cancel_checker and cancel_checker():
            break

        if send_progress:
            send_progress(f"正在爬取第 {page_num} 页...")

        html = _fetch_page_html(current_url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        page_profs = _extract_from_page(soup, selectors, affiliation, current_url)

        new_count = 0
        for prof in page_profs:
            name_key = prof["name"].strip().lower()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                results.append(prof)
                new_count += 1

        if send_progress:
            send_progress(f"第 {page_num} 页提取 {new_count} 位教授，共 {len(results)} 位")

        # Check for next page
        next_sel = selectors.get("pagination_next")
        if not next_sel:
            break

        next_link = soup.select_one(next_sel)
        if not next_link:
            break

        href = next_link.get("href", "")
        if not href:
            break

        current_url = urljoin(current_url, str(href))
        if delay > 0:
            time.sleep(delay)

    return results


def _fetch_ajax_content(page_url: str, ajax_config: dict) -> str:
    """Fetch content via AJAX endpoint with session cookies.

    First visits the page URL to establish a session, then makes the AJAX
    request with the configured parameters.

    Args:
        page_url: The main page URL (to establish session).
        ajax_config: Dict with keys: url, method, params, response_field.

    Returns:
        HTML content string from the AJAX response.
    """
    import requests as req

    ajax_url = ajax_config.get("url", "")
    if not ajax_url:
        return ""

    # Resolve relative URLs
    if not ajax_url.startswith("http"):
        ajax_url = urljoin(page_url, ajax_url)

    method = ajax_config.get("method", "POST").upper()
    params = ajax_config.get("params", {})
    response_field = ajax_config.get("response_field", "content")

    session = req.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    })

    try:
        # Visit the page first to establish session cookies
        session.get(page_url, timeout=30)

        # Make the AJAX request
        headers = {
            "Referer": page_url,
            "X-Requested-With": "XMLHttpRequest",
        }

        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            resp = session.post(ajax_url, data=params, headers=headers, timeout=30)
        else:
            resp = session.get(ajax_url, params=params, headers=headers, timeout=30)

        resp.raise_for_status()

        # Try to parse as JSON and extract the content field
        try:
            data = resp.json()
            if isinstance(data, dict) and response_field in data:
                return data[response_field]
            elif isinstance(data, str):
                return data
        except (json.JSONDecodeError, ValueError):
            pass

        # Return raw text if not JSON
        return resp.text

    except Exception:
        logger.exception("AJAX fetch failed for %s", ajax_url)
        return ""


def _fetch_page_html(url: str) -> str:
    """Fetch raw HTML using crawl4ai with auto_tab_click for dynamic pages."""
    try:
        from .engine import crawl_url_full
        result = crawl_url_full(url, auto_tab_click=True)
        if result.html:
            return result.html
    except Exception:
        logger.exception("Failed to fetch %s", url)

    # Fallback to requests
    try:
        import requests
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except Exception:
        logger.exception("Fallback requests also failed for %s", url)
        return ""


def _extract_from_page(
    soup: BeautifulSoup,
    selectors: dict,
    affiliation: str,
    base_url: str,
) -> list[dict]:
    """Extract professor data from a single parsed page."""
    results: list[dict] = []

    card_selector = selectors.get("card")
    name_selector = selectors.get("name", "")

    if not name_selector:
        logger.warning("No 'name' selector provided")
        return results

    if card_selector:
        cards = soup.select(card_selector)
        for card in cards:
            prof = _extract_card(card, selectors, affiliation, base_url)
            if prof and prof.get("name"):
                results.append(prof)
    else:
        # No card selector — find all name elements directly
        name_elements = soup.select(name_selector)
        for name_el in name_elements:
            prof = _extract_from_name_element(name_el, selectors, affiliation, base_url)
            if prof and prof.get("name"):
                results.append(prof)

    return results


def _extract_card(
    card,
    selectors: dict,
    affiliation: str,
    base_url: str,
) -> dict:
    """Extract professor info from a card element."""
    prof: dict = {"affiliation": affiliation}

    # Name (required)
    name_sel = selectors.get("name", "")
    if name_sel:
        name_el = card.select_one(name_sel)
        if name_el:
            prof["name"] = name_el.get_text(strip=True)
        else:
            return {}

    # Profile URL
    url_sel = selectors.get("profile_url")
    if url_sel:
        url_el = card.select_one(url_sel)
        if url_el:
            href = url_el.get("href", "")
            if href:
                prof["url"] = urljoin(base_url, str(href))

    # Title
    title_sel = selectors.get("title")
    if title_sel:
        title_el = card.select_one(title_sel)
        if title_el:
            prof["title"] = title_el.get_text(strip=True)

    # Email
    email_sel = selectors.get("email")
    if email_sel:
        email_el = card.select_one(email_sel)
        if email_el:
            email = _extract_email(email_el)
            if email:
                prof["email"] = email

    # Research interests
    interests_sel = selectors.get("research_interests")
    if interests_sel:
        int_el = card.select_one(interests_sel)
        if int_el:
            text = int_el.get_text(strip=True)
            interests = [
                s.strip()
                for s in re.split(r"[,;，；、/|]", text)
                if s.strip()
            ]
            if interests:
                prof["research_interests"] = interests

    # Photo
    photo_sel = selectors.get("photo_url")
    if photo_sel:
        photo_el = card.select_one(photo_sel)
        if photo_el:
            src = photo_el.get("src", "")
            if src:
                prof["photo_url"] = urljoin(base_url, str(src))

    return prof


def _extract_from_name_element(
    name_el,
    selectors: dict,
    affiliation: str,
    base_url: str,
) -> dict:
    """Extract professor info starting from a name element (no card container)."""
    prof: dict = {"affiliation": affiliation, "name": name_el.get_text(strip=True)}

    # Try to find a link from the name element itself or its parent
    link = name_el if name_el.name == "a" else name_el.find("a")
    if link and link.get("href"):
        prof["url"] = urljoin(base_url, str(link["href"]))

    return prof


def _extract_email(element) -> Optional[str]:
    """Extract email from an element (mailto: link or text)."""
    # Check for mailto: link
    if element.name == "a":
        href = element.get("href", "")
        if href.startswith("mailto:"):
            return href[7:]

    a_tag = element.find("a") if hasattr(element, "find") else None
    if a_tag:
        href = a_tag.get("href", "")
        if href.startswith("mailto:"):
            return href[7:]

    # Try text content — look for email pattern
    text = element.get_text(strip=True) if hasattr(element, "get_text") else str(element)
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)

    return None
