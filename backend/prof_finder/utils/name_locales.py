"""Merge professor name_locales from trusted external sources (no pinyin inference)."""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

from .professor_dedup import has_cjk

LocaleKey = Literal["zh", "en"]
_MAX_LEN = 200


def classify_name_locale(text: str) -> Optional[LocaleKey]:
    """Classify a name string as Chinese (CJK) or English (Latin)."""
    s = (text or "").strip()
    if not s:
        return None
    if has_cjk(s):
        return "zh"
    if re.search(r"[A-Za-z]", s):
        return "en"
    return None


def normalize_english_name(text: str) -> str:
    """Normalize Latin author names for storage (e.g. 'Zhang, Wei' -> 'Zhang Wei')."""
    s = re.sub(r"\s+", " ", (text or "").strip())
    if "," in s:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) == 2:
            return f"{parts[0]} {parts[1]}"[:_MAX_LEN]
    return s[:_MAX_LEN]


def _trim_locale_value(text: str, locale: LocaleKey) -> str:
    s = (text or "").strip()
    if locale == "en":
        s = normalize_english_name(s)
    return s[:_MAX_LEN]


def infer_locales_from_name(name: str) -> dict[str, str]:
    """Infer a single locale entry from the primary name field."""
    s = (name or "").strip()
    if not s:
        return {}
    kind = classify_name_locale(s)
    if kind == "zh":
        return {"zh": s[:_MAX_LEN]}
    if kind == "en":
        return {"en": normalize_english_name(s)}
    return {}


def merge_name_locales(
    professor: Any,
    *,
    zh: Optional[str] = None,
    en: Optional[str] = None,
) -> bool:
    """Fill empty name_locales slots; never overwrite user-provided values.

    Returns True if professor.name_locales was modified.
    """
    locales: dict[str, str] = dict(professor.name_locales or {})
    changed = False

    if zh:
        z = _trim_locale_value(zh, "zh")
        if classify_name_locale(z) == "zh" and not (locales.get("zh") or "").strip():
            locales["zh"] = z
            changed = True

    if en:
        e = _trim_locale_value(en, "en")
        if classify_name_locale(e) == "en" and not (locales.get("en") or "").strip():
            locales["en"] = e
            changed = True

    if changed:
        professor.name_locales = locales
    return changed


def apply_inferred_locales_from_name(professor: Any) -> bool:
    """Merge infer_locales_from_name(professor.name) into empty slots."""
    inferred = infer_locales_from_name(getattr(professor, "name", "") or "")
    if not inferred:
        return False
    return merge_name_locales(
        professor,
        zh=inferred.get("zh"),
        en=inferred.get("en"),
    )


def has_stored_name(name: Optional[str]) -> bool:
    """True when the professor already has a non-empty display name."""
    return bool((name or "").strip())


def apply_external_name(professor: Any, incoming: Optional[str]) -> None:
    """Set professor.name from DBLP/Scholar only when it is not already set."""
    if has_stored_name(getattr(professor, "name", None)):
        return
    incoming_val = (incoming or "").strip()
    if incoming_val:
        professor.name = incoming_val


def apply_scholar_name_update(professor: Any, scholar_name: Optional[str]) -> None:
    """Apply Scholar author name; keep existing professor.name when set."""
    incoming = (scholar_name or "").strip() or None
    if has_stored_name(professor.name):
        old_name = (professor.name or "").strip()
        if has_cjk(old_name):
            merge_name_locales(professor, zh=old_name)
        merge_name_locales(professor, en=incoming)
        return
    if incoming:
        professor.name = incoming
    merge_name_locales(professor, en=incoming)
    apply_inferred_locales_from_name(professor)


def apply_dblp_name_update(professor: Any, dblp_name: Optional[str]) -> None:
    """Apply DBLP author name; keep existing professor.name when set."""
    incoming = (dblp_name or "").strip() or None
    if has_stored_name(professor.name):
        merge_name_locales(professor, en=incoming)
        return
    if incoming:
        professor.name = incoming
    merge_name_locales(professor, en=incoming)
    apply_inferred_locales_from_name(professor)
