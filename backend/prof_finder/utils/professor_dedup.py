"""Professor duplicate detection using university name variants and pinyin names."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from ..models.schema import Professor, University

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def university_keywords(
    university_variants: list[str] | None,
    *,
    university_full_name: str | None = None,
    department_affiliation: str | None = None,
) -> list[str]:
    """Build keyword list for matching affiliations to a university."""
    keywords: list[str] = []
    seen: set[str] = set()
    for raw in list(university_variants or []):
        if not raw:
            continue
        key = raw.strip().lower()
        if key not in seen:
            seen.add(key)
            keywords.append(raw.strip())
    for extra in (university_full_name, department_affiliation):
        if not extra:
            continue
        key = extra.strip().lower()
        if key not in seen:
            seen.add(key)
            keywords.append(extra.strip())
    return keywords


def affiliation_keyword_hits(affiliation: str, keywords: list[str]) -> int:
    if not affiliation or not keywords:
        return 0
    aff_lower = affiliation.lower()
    return sum(1 for kw in keywords if kw.lower() in aff_lower)


def affiliations_same_university(
    aff1: str | None,
    aff2: str | None,
    *,
    university_variants: list[str] | None = None,
    university_full_name: str | None = None,
    department_affiliation: str | None = None,
) -> bool:
    """Return True when two affiliation strings refer to the same university."""
    a1 = (aff1 or "").strip()
    a2 = (aff2 or "").strip()
    if not a1 and not a2:
        return True
    if not a1 or not a2:
        return False
    if a1 == a2:
        return True
    a1l, a2l = a1.lower(), a2.lower()
    if a1l in a2l or a2l in a1l:
        return True

    keywords = university_keywords(
        university_variants,
        university_full_name=university_full_name,
        department_affiliation=department_affiliation,
    )
    if not keywords:
        return False
    return (
        affiliation_keyword_hits(a1, keywords) > 0
        and affiliation_keyword_hits(a2, keywords) > 0
    )


def names_match(name_a: str, name_b: str) -> bool:
    """Match Chinese/English name forms, including pinyin variants."""
    a = (name_a or "").strip()
    b = (name_b or "").strip()
    if not a or not b:
        return False
    if a == b:
        return True

    from ..crawler.scholar_matcher import _name_matches, generate_search_terms

    if has_cjk(a) and not has_cjk(b):
        for term in generate_search_terms(a):
            if _name_matches(term, b):
                return True
    if has_cjk(b) and not has_cjk(a):
        for term in generate_search_terms(b):
            if _name_matches(term, a):
                return True
    return _name_matches(a, b)


def affiliations_match_with_any_university(
    aff1: str | None,
    aff2: str | None,
    universities: list[University],
) -> bool:
    """True if affiliations match via any registered university's variants."""
    if affiliations_same_university(aff1, aff2):
        return True
    for uni in universities:
        if affiliations_same_university(
            aff1,
            aff2,
            university_variants=list(uni.name_variants or []),
            university_full_name=uni.full_name,
        ):
            return True
    return False


def _affiliation_pair_matches(
    aff1: str | None,
    aff2: str | None,
    *,
    university_variants: list[str] | None,
    university_full_name: str | None,
    department_affiliation: str | None,
    universities: list[University] | None,
) -> bool:
    if affiliations_same_university(
        aff1,
        aff2,
        university_variants=university_variants,
        university_full_name=university_full_name,
        department_affiliation=department_affiliation,
    ):
        return True
    if universities:
        return affiliations_match_with_any_university(aff1, aff2, universities)
    return False


def find_matching_professor(
    session: Session,
    user_id: int,
    name: str,
    affiliation: str | None,
    *,
    university_variants: list[str] | None = None,
    university_full_name: str | None = None,
    department_affiliation: str | None = None,
    universities: list[University] | None = None,
) -> Optional[Professor]:
    """Find an existing professor that should be treated as the same person."""
    from ..models.schema import Professor

    affiliation_val = (affiliation or "").strip() or None
    base = session.query(Professor).filter(Professor.user_id == user_id)

    if affiliation_val:
        exact = base.filter(
            Professor.name == name,
            Professor.affiliation == affiliation_val,
        ).first()
    else:
        exact = base.filter(
            Professor.name == name,
            Professor.affiliation.is_(None),
        ).first()
    if exact:
        return exact

    keywords = university_keywords(
        university_variants,
        university_full_name=university_full_name,
        department_affiliation=department_affiliation,
    )
    has_uni_hints = bool(keywords or universities)
    if not has_uni_hints and not has_cjk(name):
        return None

    def affiliation_matches(prof: Professor) -> bool:
        if not has_uni_hints:
            return affiliation_val == ((prof.affiliation or "").strip() or None)
        return _affiliation_pair_matches(
            affiliation_val,
            prof.affiliation,
            university_variants=university_variants,
            university_full_name=university_full_name,
            department_affiliation=department_affiliation,
            universities=universities,
        )

    for prof in base.filter(Professor.name == name).all():
        if names_match(name, prof.name) and affiliation_matches(prof):
            return prof

    if not has_cjk(name):
        return None

    for prof in base.all():
        if prof.name == name:
            continue
        if names_match(name, prof.name) and affiliation_matches(prof):
            return prof
    return None


def find_name_collision_groups(
    professors: list[Professor],
    universities: list[University],
) -> list[dict]:
    """Group professors that share a name (or pinyin form) at the same university.

    Returns list of dicts: {display_name, professor_ids, affiliations, reason}.
    """
    groups: list[list[Professor]] = []

    for prof in professors:
        placed = False
        for group in groups:
            anchor = group[0]
            if not names_match(prof.name, anchor.name):
                continue
            if affiliations_match_with_any_university(
                prof.affiliation, anchor.affiliation, universities
            ):
                group.append(prof)
                placed = True
                break
        if not placed:
            groups.append([prof])

    collisions: list[dict] = []
    for group in groups:
        if len(group) < 2:
            continue
        ids = [p.id for p in group]
        affiliations = [p.affiliation for p in group if p.affiliation]
        collisions.append(
            {
                "display_name": group[0].name,
                "professor_ids": ids,
                "affiliations": affiliations,
                "reason": "same_name_same_university",
            }
        )
    return collisions
