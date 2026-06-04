"""Scholar matching module — find a professor's Google Scholar profile.

Workflow:
  1. Convert Chinese name to pinyin search terms (handling compound surnames & polyphones)
  2. Search Google Scholar incrementally with name × university variants
  3. Verify candidates with rule-based scoring (name + affiliation + email domain)
  4. Return early on high-confidence match; accumulate ambiguous candidates
"""

import logging
import re
import time
from typing import Optional

from pypinyin import Style, pinyin

logger = logging.getLogger(__name__)

# Common compound surnames (复姓) — used to correctly split Chinese names
_COMPOUND_SURNAMES: set[str] = {
    "欧阳", "司马", "上官", "诸葛", "公孙", "慕容", "令狐", "皇甫", "端木",
    "东方", "独孤", "南宫", "西门", "长孙", "百里", "轩辕", "宇文", "夏侯",
    "尉迟", "钟离", "鲜于", "闻人", "太叔", "亓官", "谷梁", "壤驷", "公良",
    "段干", "呼延", "子车", "颛孙", "公西", "乐正", "公冶", "濮阳", "单于",
    "拓跋", "夹谷", "漆雕", "公羊", "左丘", "微生", "梁丘", "东郭", "第五",
    "南门", "司徒", "司空", "司寇", "司士", "王孙", "公祖", "贯丘", "公伯",
    "公乘", "公仪", "公户", "公山", "公坚", "公肩", "公皙", "公綦", "公叔",
    "公孟", "公明", "公玉", "公若", "仲孙", "孟孙", "叔孙", "季孙", "士孙",
}


def _split_chinese_name(name: str) -> tuple[str, str]:
    """Split a Chinese name into (surname, given_name).

    Handles compound surnames like 欧阳, 司马 etc.
    Returns (surname, given_name) as Chinese strings.
    """
    name = name.strip()
    # Try compound surname first (2-char prefix)
    if len(name) >= 3:
        prefix2 = name[:2]
        if prefix2 in _COMPOUND_SURNAMES:
            return prefix2, name[2:]
    # Single-character surname
    if len(name) >= 2:
        return name[0], name[1:]
    return name, ""


def _to_pinyin_variants(text: str) -> list[str]:
    """Convert Chinese text to all pinyin combinations (handling polyphones).

    Returns up to 4 most likely combinations.
    """
    if not text:
        return [""]

    # Each character → list of possible readings
    char_readings: list[list[str]] = []
    for char in text:
        readings = pinyin(char, style=Style.NORMAL, heteronym=True)
        # readings is like [['ceng', 'zeng']] for a single char
        # Each inner list contains all readings for that character
        flat = readings[0] if readings else [char]
        char_readings.append(flat)

    # Generate all combinations, cap at 4
    combos = _combine_readings(char_readings, max_results=4)
    return combos


def _combine_readings(char_readings: list[list[str]], max_results: int = 4) -> list[str]:
    """Generate pinyin combinations from per-character readings, capped."""
    if not char_readings:
        return [""]

    results = [""]
    for readings in char_readings:
        new_results = []
        for combo in results:
            for reading in readings:
                new_results.append(f"{combo}{reading}".strip())
        results = new_results
        # Prune: keep only top max_results by frequency (first reading is most common)
        if len(results) > max_results * 2:
            results = results[:max_results * 2]

    return results[:max_results]


def _capitalize_first(s: str) -> str:
    """Capitalize first letter of each word."""
    return " ".join(w.capitalize() for w in s.split())


def generate_search_terms(chinese_name: str) -> list[str]:
    """Generate English name search terms from a Chinese name.

    Handles:
    - Compound surnames (复姓): 欧阳明 → "Ouyang Ming", "Ming Ouyang"
    - Polyphones (多音字): 曾乐琪 → multiple readings
    - Two name orders: "Surname, Given" and "Given Surname"

    Returns up to 4 unique search terms.
    """
    surname_cn, given_cn = _split_chinese_name(chinese_name)
    if not given_cn:
        # Single character name — just return pinyin
        return _to_pinyin_variants(surname_cn)[:4]

    surname_variants = _to_pinyin_variants(surname_cn)
    given_variants = _to_pinyin_variants(given_cn)

    terms: list[str] = []
    seen: set[str] = set()

    # Generate combinations: up to 4 surname × given pairs
    max_combos = 4
    count = 0
    for sv in surname_variants:
        for gv in given_variants:
            if count >= max_combos:
                break
            s_cap = sv.capitalize()
            g_cap = gv.capitalize()
            # Order 1: "Zhang, Wei"
            term1 = f"{s_cap}, {g_cap}"
            if term1.lower() not in seen:
                seen.add(term1.lower())
                terms.append(term1)
                count += 1
            # Order 2: "Wei Zhang"
            term2 = f"{g_cap} {s_cap}"
            if term2.lower() not in seen and count < max_combos:
                seen.add(term2.lower())
                terms.append(term2)
                count += 1
        if count >= max_combos:
            break

    return terms[:4]


def _normalize_for_match(s: str) -> str:
    """Normalize a string for loose comparison."""
    return re.sub(r"[,\s]+", " ", s.strip().lower())


def _name_matches(search_term: str, scholar_name: str) -> bool:
    """Check if a search term matches a Scholar author name.

    Handles variations like "Zhang Wei" vs "Wei Zhang" vs "Zhang, Wei".
    """
    a = _normalize_for_match(search_term)
    b = _normalize_for_match(scholar_name)
    if a == b:
        return True
    # Split into tokens and check if they're the same set
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    return a_tokens == b_tokens


def _affiliation_matches(
    scholar_affiliation: str,
    university_variants: list[str],
    department_affiliation: Optional[str] = None,
) -> tuple[bool, int]:
    """Check if a Scholar affiliation matches the expected university.

    Returns (matched, hit_count) — hit_count is how many variant keywords
    appear in the affiliation.
    """
    from ..utils.professor_dedup import affiliation_keyword_hits, university_keywords

    if not scholar_affiliation:
        return False, 0

    keywords = university_keywords(
        university_variants,
        department_affiliation=department_affiliation,
    )
    hits = affiliation_keyword_hits(scholar_affiliation, keywords)
    return hits > 0, hits


def _extract_domain(value: str) -> str:
    """Extract domain from an email address or a bare domain string.

    Handles both formats returned by scholarly:
    - Full email: "user@xjtu.edu.cn" → "xjtu.edu.cn"
    - Bare domain: "xjtu.edu.cn" → "xjtu.edu.cn"
    """
    value = value.strip().lower()
    if "@" in value:
        parts = value.split("@")
        return parts[-1] if len(parts) == 2 else ""
    # Bare domain — accept if it looks like a domain (contains a dot)
    return value if "." in value else ""


def _email_domain_matches(scholar_email: Optional[str], crawled_email: Optional[str]) -> bool:
    """Check if email domains match between Scholar and crawled data."""
    if not scholar_email or not crawled_email:
        return False

    return _extract_domain(scholar_email) == _extract_domain(crawled_email)


def _score_candidate(
    search_term: str,
    scholar_name: str,
    scholar_affiliation: str,
    scholar_email: Optional[str],
    crawled_email: Optional[str],
    university_variants: list[str],
    department_affiliation: Optional[str],
) -> tuple[int, bool]:
    """Score a Scholar candidate. Returns (score, email_domain_match).

    Score breakdown:
      - Name match: 40 points
      - Affiliation match: 40 points (scaled by hit count, max 60)
      - Email domain match: 20 points (also returned as boolean for one-vote-pass)
    """
    score = 0

    # Name
    if _name_matches(search_term, scholar_name):
        score += 40

    # Affiliation
    aff_matched, aff_hits = _affiliation_matches(
        scholar_affiliation, university_variants, department_affiliation
    )
    if aff_matched:
        score += min(40 + (aff_hits - 1) * 10, 60)

    # Email domain
    email_match = _email_domain_matches(scholar_email, crawled_email)
    if email_match:
        score += 20

    return score, email_match


def match_professor_scholar(
    chinese_name: str,
    crawled_email: Optional[str],
    university_variants: list[str],
    department_affiliation: Optional[str],
    scholar_crawler,
    request_delay: float = 3.0,
    cancel_checker=None,
) -> dict:
    """Search Google Scholar for a professor and verify the match.

    Args:
        chinese_name: Professor's Chinese name (e.g. "张伟").
        crawled_email: Email from school website (e.g. "zhangwei@xjtu.edu.cn").
        university_variants: LLM-generated university name variants.
        department_affiliation: e.g. "西安交通大学计算机科学与技术学院".
        scholar_crawler: ScholarCrawler instance.
        request_delay: Seconds between Scholar API calls.
        cancel_checker: Optional callable returning True to abort.

    Returns:
        {
            "status": "matched" | "ambiguous" | "not_found",
            "scholar_id": str | None,          # if matched
            "scholar_name": str | None,
            "scholar_affiliation": str | None,
            "candidates": list[dict],           # if ambiguous
        }
    """
    search_terms = generate_search_terms(chinese_name)
    logger.info(
        "Scholar match for '%s': generated %d search terms: %s",
        chinese_name, len(search_terms), search_terms,
    )
    if not search_terms:
        return {"status": "not_found", "scholar_id": None, "candidates": []}

    seen_ids: set[str] = set()
    candidates: list[dict] = []
    EMAIL_MATCH_THRESHOLD = 80  # auto-accept score when email matches
    # Accept any name-matching candidate (score >= 40).  Previously 80 was
    # too strict — professors who changed institutions would only get 40
    # (name) and be discarded even though they were the right person.
    SCORE_THRESHOLD = 40
    MAX_CANDIDATES = 5

    for term in search_terms:
        if cancel_checker and cancel_checker():
            break

        try:
            results = scholar_crawler.search_author(term, limit=5)
            logger.info("Scholar search for '%s' returned %d raw results", term, len(results))
        except Exception as e:
            logger.warning("Scholar search failed for '%s': %s", term, e)
            results = []

        for result in results:
            if cancel_checker and cancel_checker():
                break

            sid = result.get("scholar_id", "")
            if not sid or sid in seen_ids:
                continue
            seen_ids.add(sid)

            scholar_name = result.get("name", "")
            scholar_aff = result.get("affiliation", "")
            scholar_email = result.get("email")

            score, email_match = _score_candidate(
                search_term=term,
                scholar_name=scholar_name,
                scholar_affiliation=scholar_aff,
                scholar_email=scholar_email,
                crawled_email=crawled_email,
                university_variants=university_variants,
                department_affiliation=department_affiliation,
            )

            # Need at least name match to be a valid candidate
            if score < SCORE_THRESHOLD:
                logger.debug(
                    "Candidate '%s' (id=%s, aff='%s') rejected: score=%d < threshold=%d",
                    scholar_name, sid, scholar_aff, score, SCORE_THRESHOLD,
                )
                continue

            candidate = {
                "scholar_id": sid,
                "name": scholar_name,
                "affiliation": scholar_aff,
                "score": score,
                "email_domain_match": email_match,
                "citedby": result.get("citedby", 0),
            }

            # Email domain match → immediate return
            if email_match:
                return {
                    "status": "matched",
                    "scholar_id": sid,
                    "scholar_name": scholar_name,
                    "scholar_affiliation": scholar_aff,
                    "candidates": [candidate],
                }

            candidates.append(candidate)

            # Single high-score candidate → can return early
            if len(candidates) >= MAX_CANDIDATES:
                break

        if len(candidates) >= MAX_CANDIDATES:
            break

        # Delay between search calls
        if request_delay > 0:
            time.sleep(request_delay)

    if not candidates:
        logger.warning("Scholar match for '%s': no candidates found (all search terms returned 0 results or all candidates scored below threshold)", chinese_name)
        return {"status": "not_found", "scholar_id": None, "candidates": []}

    if len(candidates) == 1:
        c = candidates[0]
        return {
            "status": "matched",
            "scholar_id": c["scholar_id"],
            "scholar_name": c["name"],
            "scholar_affiliation": c["affiliation"],
            "candidates": candidates,
        }

    # Multiple candidates — sort by score then citations
    candidates.sort(key=lambda c: (c["score"], c.get("citedby", 0)), reverse=True)
    return {
        "status": "ambiguous",
        "scholar_id": None,
        "candidates": candidates,
    }
