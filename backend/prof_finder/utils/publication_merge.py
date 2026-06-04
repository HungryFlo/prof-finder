"""Merge professor publications from multiple external sources."""

from __future__ import annotations

import re
from typing import Optional


def normalize_title(title: str) -> str:
    """Normalize title for cross-source deduplication."""
    if not title:
        return ""
    s = title.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def _pub_source(pub: dict) -> str:
    raw = pub.get("source")
    if raw in ("scholar", "dblp"):
        return raw
    if pub.get("author_pub_id") or pub.get("gscholar_url"):
        return "scholar"
    if pub.get("dblp_url"):
        return "dblp"
    return raw or "unknown"


def _scholar_richness(pub: dict) -> int:
    score = 0
    if pub.get("abstract"):
        score += 2
    if pub.get("citations"):
        score += 1
    if pub.get("author_pub_id"):
        score += 1
    return score


def _pick_better(existing: dict, candidate: dict) -> dict:
    if _scholar_richness(candidate) > _scholar_richness(existing):
        return candidate
    if _scholar_richness(candidate) < _scholar_richness(existing):
        return existing
    if _pub_source(candidate) == "scholar" and _pub_source(existing) != "scholar":
        return candidate
    return existing


def merge_publications(
    existing: Optional[list[dict]],
    incoming: list[dict],
    source: str,
) -> list[dict]:
    """Replace publications for ``source``, merge with other sources, dedupe by title."""
    other: list[dict] = []
    for pub in existing or []:
        if isinstance(pub, dict) and _pub_source(pub) != source:
            other.append(pub)

    incoming_tagged: list[dict] = []
    for pub in incoming:
        if not isinstance(pub, dict):
            continue
        item = dict(pub)
        item["source"] = source
        incoming_tagged.append(item)

    merged = other + incoming_tagged
    by_title: dict[str, dict] = {}
    untitled: list[dict] = []

    for pub in merged:
        key = normalize_title(pub.get("title") or "")
        if not key:
            untitled.append(pub)
            continue
        if key not in by_title:
            by_title[key] = pub
        else:
            by_title[key] = _pick_better(by_title[key], pub)

    return untitled + list(by_title.values())


def publications_for_source(publications: Optional[list[dict]], source: str) -> list[dict]:
    """Return publications tagged with a given source."""
    return [p for p in (publications or []) if isinstance(p, dict) and _pub_source(p) == source]
