"""URL helpers — resolve relative links for storage and crawling."""

from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin, urlparse

_ABSOLUTE_SCHEMES = ("http://", "https://", "file://", "raw:")

_HOMEPAGE_KEYS = ("homepage", "url", "photo_url", "source_url")


def resolve_absolute_url(url: str, base_url: str) -> str:
    """Return an absolute URL; join relative paths with ``base_url``."""
    raw = (url or "").strip()
    if not raw:
        return ""
    lower = raw.lower()
    if lower.startswith(_ABSOLUTE_SCHEMES):
        return raw
    base = (base_url or "").strip()
    if not base:
        return raw
    parsed_base = urlparse(base)
    if not parsed_base.scheme:
        return raw
    return urljoin(base, raw)


def resolve_optional_url(url: Optional[str], base_url: str) -> Optional[str]:
    """Like :func:`resolve_absolute_url` but returns ``None`` for empty input."""
    resolved = resolve_absolute_url(url or "", base_url)
    return resolved or None


def infer_crawl_base_url(professors: list[dict], fallback: str = "") -> str:
    """Guess site origin from crawled professor URLs when no list URL is available."""
    if (fallback or "").strip():
        return fallback.strip()
    for prof in professors:
        for key in _HOMEPAGE_KEYS:
            val = (prof.get(key) or "").strip()
            if not val.lower().startswith(("http://", "https://")):
                continue
            parsed = urlparse(val)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
    return ""


def normalize_school_crawl_professor(prof: dict, base_url: str) -> None:
    """Resolve relative homepage-related URLs in a professor dict before DB insert."""
    base = (base_url or "").strip() or infer_crawl_base_url([prof])
    if not base:
        return
    for key in _HOMEPAGE_KEYS:
        val = prof.get(key)
        if val and isinstance(val, str):
            resolved = resolve_absolute_url(val.strip(), base)
            if resolved:
                prof[key] = resolved
    if not (prof.get("homepage") or "").strip():
        url_val = (prof.get("url") or "").strip()
        if url_val:
            prof["homepage"] = resolve_absolute_url(url_val, base)


def normalize_school_crawl_professors(
    professors: list[dict],
    base_url: str,
) -> list[dict]:
    """Normalize homepage URLs for all professors in a school crawl batch."""
    base = (base_url or "").strip() or infer_crawl_base_url(professors)
    if not base:
        return professors
    for prof in professors:
        normalize_school_crawl_professor(prof, base)
    return professors
