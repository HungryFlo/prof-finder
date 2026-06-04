"""Merge crawled professor profile fields without losing existing data."""

from __future__ import annotations

from typing import Any, Optional


_NOTES_SEP = "\n\n---\n\n"


def _norm_email(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _norm_interests(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.replace(";", ",").split(",") if p.strip()]
        return parts
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def _append_note(existing: Optional[str], fragment: str) -> str:
    fragment = fragment.strip()
    if not fragment:
        return (existing or "").strip()
    base = (existing or "").strip()
    if not base:
        return fragment
    if fragment in base:
        return base
    return f"{base}{_NOTES_SEP}{fragment}"


def _merge_interests(existing: list[str], new_items: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in list(existing or []) + list(new_items or []):
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item.strip())
    return merged


def merge_profile_fields(
    *,
    email: Optional[str] = None,
    research_interests: Optional[list[str]] = None,
    manual_notes: Optional[str] = None,
    homepage: Optional[str] = None,
    extracted: dict,
) -> dict[str, Any]:
    """Merge LLM-extracted profile data into existing professor fields.

    Returns dict with keys: email, research_interests, manual_notes, homepage.
    """
    out_email = _norm_email(email)
    crawled_email = _norm_email(extracted.get("email"))
    notes = (manual_notes or "").strip() or None

    if crawled_email:
        if not out_email:
            out_email = crawled_email
        elif out_email.lower() != crawled_email.lower():
            notes = _append_note(notes, f"爬取邮箱: {crawled_email}")

    merged_interests = _merge_interests(
        _norm_interests(research_interests),
        _norm_interests(extracted.get("research_interests")),
    )

    title = (extracted.get("title") or "").strip()
    if title:
        notes = _append_note(notes, f"职称: {title}")

    bio = (extracted.get("bio") or "").strip()
    if bio:
        notes = _append_note(notes, bio)

    external = (extracted.get("external_homepage") or "").strip()
    profile_url = (homepage or "").strip()
    if external and external != profile_url:
        notes = _append_note(notes, f"外部主页: {external}")

    return {
        "email": out_email,
        "research_interests": merged_interests,
        "manual_notes": notes,
        "homepage": profile_url or homepage,
    }


def merge_profile_into_dict(prof: dict, extracted: dict) -> dict:
    """Merge extracted profile into a professor dict (batch crawl)."""
    merged = merge_profile_fields(
        email=prof.get("email"),
        research_interests=prof.get("research_interests"),
        manual_notes=prof.get("manual_notes"),
        homepage=prof.get("homepage") or prof.get("url"),
        extracted=extracted,
    )
    prof["email"] = merged["email"]
    prof["research_interests"] = merged["research_interests"]
    if merged.get("manual_notes"):
        prof["manual_notes"] = merged["manual_notes"]
    if merged.get("homepage"):
        prof["homepage"] = merged["homepage"]
    return prof


def apply_profile_merge_to_professor(professor: Any, extracted: dict) -> None:
    """Apply merge to a Professor ORM instance in place."""
    merged = merge_profile_fields(
        email=professor.email,
        research_interests=list(professor.research_interests or []),
        manual_notes=professor.manual_notes,
        homepage=professor.homepage,
        extracted=extracted,
    )
    professor.email = merged["email"]
    professor.research_interests = merged["research_interests"]
    professor.manual_notes = merged["manual_notes"]
    if merged.get("homepage"):
        professor.homepage = merged["homepage"]
