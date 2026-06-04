"""DBLP profile matching — mirrors scholar_matcher scoring against DBLP search."""

from __future__ import annotations

import logging
import time
from typing import Optional

from .dblp import DblpClient, _DBLP_MIN_REQUEST_DELAY, dblp_profile_url
from .scholar_matcher import (
    _affiliation_matches,
    _name_matches,
    generate_search_terms,
)

logger = logging.getLogger(__name__)


def _score_dblp_candidate(
    search_term: str,
    candidate_name: str,
    affiliations: list[str],
    crawled_email: Optional[str],
    university_variants: list[str],
    department_affiliation: Optional[str],
) -> tuple[int, bool]:
    score = 0
    if _name_matches(search_term, candidate_name):
        score += 40

    aff_text = "; ".join(affiliations)
    aff_matched, aff_hits = _affiliation_matches(
        aff_text, university_variants, department_affiliation
    )
    if aff_matched:
        score += min(40 + (aff_hits - 1) * 10, 60)

    email_match = False
    return score, email_match


def match_professor_dblp(
    chinese_name: str,
    crawled_email: Optional[str],
    university_variants: list[str],
    department_affiliation: Optional[str],
    dblp_client: DblpClient,
    request_delay: float = 3.0,
    cancel_checker=None,
) -> dict:
    """Search DBLP for a professor and return match status."""
    search_terms = generate_search_terms(chinese_name)
    if not search_terms:
        return {"status": "not_found", "dblp_pid": None, "candidates": []}

    seen_pids: set[str] = set()
    candidates: list[dict] = []
    SCORE_THRESHOLD = 40
    MAX_CANDIDATES = 5

    for term in search_terms:
        if cancel_checker and cancel_checker():
            break
        if request_delay > 0:
            time.sleep(max(float(request_delay), _DBLP_MIN_REQUEST_DELAY))
        try:
            results = dblp_client.search_author(term, limit=5)
        except Exception as e:
            logger.warning("DBLP search failed for %r: %s", term, e)
            results = []

        for result in results:
            if cancel_checker and cancel_checker():
                break
            pid = result.get("pid", "")
            if not pid or pid in seen_pids:
                continue
            seen_pids.add(pid)

            name = result.get("name", "")
            affs = result.get("affiliations") or []
            score, email_match = _score_dblp_candidate(
                search_term=term,
                candidate_name=name,
                affiliations=affs,
                crawled_email=crawled_email,
                university_variants=university_variants,
                department_affiliation=department_affiliation,
            )
            if score < SCORE_THRESHOLD:
                continue

            candidate = {
                "pid": pid,
                "name": name,
                "affiliation": affs[0] if affs else None,
                "affiliations": affs,
                "url": result.get("url") or dblp_profile_url(pid),
                "score": score,
                "email_domain_match": email_match,
            }
            candidates.append(candidate)
            if len(candidates) >= MAX_CANDIDATES:
                break

        if len(candidates) >= MAX_CANDIDATES:
            break

    if not candidates:
        return {"status": "not_found", "dblp_pid": None, "candidates": []}

    if len(candidates) == 1:
        c = candidates[0]
        return {
            "status": "matched",
            "dblp_pid": c["pid"],
            "dblp_name": c["name"],
            "dblp_url": c["url"],
            "candidates": candidates,
        }

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return {"status": "ambiguous", "dblp_pid": None, "candidates": candidates}
