"""Resolve university context for per-professor external profile matching (e.g. DBLP)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .professor_dedup import affiliation_keyword_hits, university_keywords

if TYPE_CHECKING:
    from ..models.schema import Professor, University


def resolve_scholar_match_params(
    professor: Professor,
    universities: list[University],
) -> tuple[list[str], Optional[str]]:
    """Return (university_variants, department_affiliation) for external profile matching."""
    affiliation = (professor.affiliation or "").strip() or None

    best_uni: University | None = None
    best_hits = 0
    for uni in universities:
        keywords = university_keywords(
            list(uni.name_variants or []),
            university_full_name=uni.full_name,
        )
        hits = affiliation_keyword_hits(affiliation or "", keywords)
        if hits > best_hits:
            best_hits = hits
            best_uni = uni

    if best_uni and best_hits > 0:
        return list(best_uni.name_variants or []), affiliation

    if affiliation:
        return [], affiliation

    return [], None
