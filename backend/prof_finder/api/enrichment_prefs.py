"""User preferences for automatic professor enrichment after save or Scholar sync."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class AutoEnrichFlags:
    """Which auto-enrichment sub-steps to run."""

    fetch_publication_details: bool
    paper_summaries: bool
    research_profile: bool


def flags_from_user_settings_row(row: Optional[Any]) -> AutoEnrichFlags:
    """Read flags from UserSettings ORM row; missing row → all enabled (legacy behavior)."""
    if row is None:
        return AutoEnrichFlags(True, True, True)
    return AutoEnrichFlags(
        fetch_publication_details=bool(
            getattr(row, "auto_enrich_on_save_fetch_publication_details", True)
        ),
        paper_summaries=bool(getattr(row, "auto_enrich_on_save_paper_summaries", True)),
        research_profile=bool(getattr(row, "auto_enrich_on_save_research_profile", True)),
    )


def planned_enrichment_step_count(
    *,
    has_scholar: bool,
    has_publications: bool,
    publications: list,
    flags: AutoEnrichFlags,
) -> int:
    """Sub-steps that would run for this professor snapshot and flags (matches task total)."""
    n = 0
    if flags.fetch_publication_details and has_scholar and bool(publications):
        n += 1
    if flags.paper_summaries and has_publications:
        n += 1
    if flags.research_profile:
        n += 1
    return n


def planned_enrichment_step_count_for_professor(professor: Any, flags: AutoEnrichFlags) -> int:
    pubs = list(professor.publications or [])
    has_pubs = bool(pubs)
    return planned_enrichment_step_count(
        has_scholar=bool(professor.google_scholar_id),
        has_publications=has_pubs,
        publications=pubs,
        flags=flags,
    )


def any_auto_enrich_substep_enabled(flags: AutoEnrichFlags) -> bool:
    """True if at least one auto-enrichment sub-step is toggled on."""
    return (
        flags.fetch_publication_details
        or flags.paper_summaries
        or flags.research_profile
    )
