"""DBLP API client — author search (JSON) and publication list (PID XML)."""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Optional
from urllib.parse import unquote, urlparse

import requests

from ..config import settings

logger = logging.getLogger(__name__)

_SEARCH_MAX_RETRIES = 3
_SEARCH_RETRY_BASE_DELAY = 5.0
# DBLP often closes idle connections when hit too quickly.
_DBLP_MIN_REQUEST_DELAY = 3.0

_USER_AGENT = "prof-finder/1.0 (+https://github.com/prof-finder)"
_SEARCH_API = "https://dblp.org/search/author/api"
_PID_XML = "https://dblp.org/pid/{pid}.xml"


def extract_dblp_pid_from_url(url_or_pid: str) -> str:
    """Extract DBLP pid from profile URL or return bare pid."""
    raw = (url_or_pid or "").strip()
    if not raw:
        raise ValueError("DBLP URL 或 pid 不能为空")

    if re.match(r"^[\w/.-]+$", raw) and "/" in raw and not raw.startswith("http"):
        return raw.strip("/")

    parsed = urlparse(raw)
    path = unquote(parsed.path or raw)
    match = re.search(r"/pid/(.+?)(?:\.html)?/?$", path, re.I)
    if match:
        return match.group(1).strip("/")

    if "dblp.org" in raw.lower() and "/pid/" in raw.lower():
        match = re.search(r"/pid/([^?\s#]+)", raw, re.I)
        if match:
            return match.group(1).strip("/").removesuffix(".html")

    raise ValueError("无法从 URL 中提取 DBLP pid，请使用 https://dblp.org/pid/... 格式")


def dblp_profile_url(pid: str) -> str:
    return f"https://dblp.org/pid/{pid.strip('/')}.html"


def _normalize_hits(data: dict) -> list[dict]:
    hits_wrapper = (data.get("result") or {}).get("hits") or {}
    hits = hits_wrapper.get("hit")
    if hits is None:
        return []
    if isinstance(hits, dict):
        return [hits]
    return list(hits)


def _notes_to_affiliations(notes: Any) -> list[str]:
    affs: list[str] = []
    if not notes:
        return affs
    note_list = notes.get("note") if isinstance(notes, dict) else notes
    if isinstance(note_list, dict):
        note_list = [note_list]
    if not isinstance(note_list, list):
        return affs
    for note in note_list:
        if not isinstance(note, dict):
            continue
        if note.get("@type") == "affiliation" and note.get("text"):
            affs.append(str(note["text"]).strip())
    return affs


def _parse_publication_element(pub: ET.Element) -> dict:
    key = pub.get("key", "")
    title = (pub.findtext("title") or "").strip()
    year = (pub.findtext("year") or "").strip()
    authors = [a.text.strip() for a in pub.findall("author") if a.text and a.text.strip()]
    venue = (
        (pub.findtext("journal") or "").strip()
        or (pub.findtext("booktitle") or "").strip()
    )
    return {
        "title": title,
        "year": year,
        "authors": ", ".join(authors),
        "venue": venue,
        "source": "dblp",
        "dblp_url": f"https://dblp.org/rec/{key}" if key else None,
        "citations": 0,
    }


class DblpClient:
    """Client for DBLP search and PID export APIs."""

    def __init__(self, request_delay: Optional[float] = None):
        configured = (
            float(request_delay)
            if request_delay is not None
            else float(settings.request_delay)
        )
        self._delay = max(configured, _DBLP_MIN_REQUEST_DELAY)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": _USER_AGENT})

    def _sleep(self) -> None:
        if self._delay > 0:
            time.sleep(self._delay)

    def search_author(self, query: str, limit: int = 10) -> list[dict]:
        """Search authors by name."""
        hits: list[dict] = []
        last_error: Optional[Exception] = None
        for attempt in range(_SEARCH_MAX_RETRIES):
            self._sleep()
            try:
                resp = self._session.get(
                    _SEARCH_API,
                    params={"q": query, "format": "json", "h": min(limit, 1000)},
                    timeout=30,
                )
                resp.raise_for_status()
                hits = _normalize_hits(resp.json())
                last_error = None
                break
            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if attempt < _SEARCH_MAX_RETRIES - 1:
                    delay = _SEARCH_RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        "DBLP author search failed for %r (attempt %d/%d): %s — retry in %.1fs",
                        query,
                        attempt + 1,
                        _SEARCH_MAX_RETRIES,
                        e,
                        delay,
                    )
                    time.sleep(delay)
                    continue
            except Exception as e:
                logger.warning("DBLP author search failed for %r: %s", query, e)
                return []
        if last_error is not None:
            logger.warning("DBLP author search failed for %r: %s", query, last_error)
            return []

        results: list[dict] = []
        for hit in hits[:limit]:
            info = hit.get("info") or {}
            name = info.get("author") or ""
            url = info.get("url") or ""
            if not name or not url:
                continue
            try:
                pid = extract_dblp_pid_from_url(url)
            except ValueError:
                continue
            results.append(
                {
                    "name": name,
                    "pid": pid,
                    "url": dblp_profile_url(pid),
                    "affiliations": _notes_to_affiliations(info.get("notes")),
                }
            )
        return results

    def get_author(self, pid: str) -> Optional[dict]:
        """Fetch author metadata and publications from PID XML export."""
        pid = pid.strip("/")
        self._sleep()
        try:
            resp = self._session.get(_PID_XML.format(pid=pid), timeout=60)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("DBLP get_author failed for %s: %s", pid, e)
            return None

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            logger.warning("DBLP XML parse failed for %s: %s", pid, e)
            return None

        name = root.get("name") or ""
        affiliations: list[str] = []
        person = root.find("person")
        if person is not None:
            for note in person.findall("note"):
                if note.get("type") == "affiliation" and note.text:
                    affiliations.append(note.text.strip())

        publications: list[dict] = []
        for r_elem in root.findall("r"):
            if len(r_elem) == 0:
                continue
            pub = r_elem[0]
            if pub.tag in (
                "article",
                "inproceedings",
                "proceedings",
                "book",
                "incollection",
                "phdthesis",
                "mastersthesis",
                "www",
            ):
                publications.append(_parse_publication_element(pub))

        return {
            "name": name,
            "affiliation": affiliations[0] if affiliations else None,
            "affiliations": affiliations,
            "publications": publications,
            "dblp_pid": pid,
            "dblp_url": dblp_profile_url(pid),
        }
