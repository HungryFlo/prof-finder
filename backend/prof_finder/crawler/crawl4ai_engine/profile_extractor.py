"""Crawl a single professor profile page and extract structured fields via LLM."""

from __future__ import annotations

import json
import logging
import time
from typing import Callable, Optional

from ...utils.profile_merge import merge_profile_into_dict
from .engine import crawl_url_full
from ...utils.url_utils import normalize_school_crawl_professor, resolve_absolute_url
from .llm_extractor import (
    _MAX_CONTENT_CHARS,
    _LLM_MAX_RETRIES,
    _LLM_RETRY_BASE_DELAY,
    _choose_best_content,
    _clean_html_for_llm,
    _try_ajax_endpoints,
)

logger = logging.getLogger(__name__)


def extract_professor_profile(
    url: str,
    *,
    name: str = "",
    affiliation: str = "",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    page_base_url: Optional[str] = None,
    send_progress: Optional[Callable[[str], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
) -> dict:
    """Crawl one profile URL and extract fields for a single professor.

    Returns dict with optional keys: email, research_interests, bio, title,
    external_homepage. Empty dict on failure.
    """
    if cancel_checker and cancel_checker():
        return {}

    crawl_url = url.strip()
    if page_base_url:
        crawl_url = resolve_absolute_url(crawl_url, page_base_url)

    if send_progress:
        send_progress("正在爬取个人主页...")

    crawl_result = crawl_url_full(crawl_url, auto_tab_click=True)
    if not crawl_result.success:
        logger.warning("Failed to crawl profile %s", url)
        return {}

    if cancel_checker and cancel_checker():
        return {}

    ajax_html = _try_ajax_endpoints(crawl_url, crawl_result.html or "")
    if ajax_html and len(ajax_html) > len(crawl_result.html or "") * 0.5:
        crawl_result.html = ajax_html

    if ajax_html and len(ajax_html) > 1000:
        content = _clean_html_for_llm(ajax_html)
    else:
        content = _choose_best_content(crawl_result.html, crawl_result.markdown)

    if not content:
        logger.warning("No content extracted from profile %s", url)
        return {}

    if send_progress:
        send_progress("正在使用 AI 分析个人主页...")

    return _llm_extract_profile(
        content,
        name=name,
        affiliation=affiliation,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def _llm_extract_profile(
    content: str,
    *,
    name: str,
    affiliation: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    from ...config import settings as app_settings

    if not api_key:
        api_key = app_settings.deepseek_api_key
    if not base_url:
        base_url = app_settings.deepseek_base_url
    if not model:
        model = getattr(app_settings, "deepseek_model", None) or "deepseek-chat"

    if not api_key:
        logger.error("No DeepSeek API key configured for profile extraction")
        return {}

    truncated = content[:_MAX_CONTENT_CHARS]
    context_name = name or "未知"
    context_aff = affiliation or "未知"

    prompt = f"""从以下教师/教授个人主页 HTML 中提取该教师的信息，返回单个 JSON 对象（不是数组）。
已知姓名：{context_name}
已知机构：{context_aff}

JSON 格式：
{{"email":"邮箱或null","research_interests":["方向1"],"bio":"个人简介或null","title":"职称或null","external_homepage":"外部个人网站URL或null"}}

只输出 JSON 对象，无其他文字。research_interests 为字符串数组，无法提取则为 []。

HTML 内容：
{truncated}
"""

    import httpx
    from openai import APIConnectionError, APITimeoutError, RateLimitError, APIStatusError, OpenAI

    last_error: Optional[Exception] = None

    for attempt in range(_LLM_MAX_RETRIES):
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(120.0, connect=30.0),
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8192,
            )
            text = response.choices[0].message.content or ""
            parsed = _parse_llm_json_object(text)
            if not isinstance(parsed.get("research_interests"), list):
                parsed["research_interests"] = _normalize_interests(parsed.get("research_interests"))
            return parsed

        except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
            last_error = exc
            if attempt < _LLM_MAX_RETRIES - 1:
                delay = _LLM_RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    "Profile LLM attempt %d/%d failed: %s — retry in %.1fs",
                    attempt + 1,
                    _LLM_MAX_RETRIES,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue
            logger.error("Profile LLM failed after retries: %s", exc)

        except APIStatusError as exc:
            if exc.status_code in (401, 403):
                logger.error("Profile LLM: invalid API key")
                return {}
            if exc.status_code == 429 and attempt < _LLM_MAX_RETRIES - 1:
                time.sleep(_LLM_RETRY_BASE_DELAY * (2**attempt))
                continue
            logger.error("Profile LLM HTTP %d: %s", exc.status_code, exc)
            return {}

        except Exception:
            logger.exception("Profile LLM extraction failed")
            return {}

    if last_error:
        logger.error("Profile LLM failed: %s", last_error)
    return {}


def _normalize_interests(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [p.strip() for p in value.replace(";", ",").split(",") if p.strip()]
    return []


def _parse_llm_json_object(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        logger.warning("No JSON object in profile LLM response")
        return {}

    try:
        result = json.loads(content[start : end + 1])
        return result if isinstance(result, dict) else {}
    except json.JSONDecodeError:
        logger.warning("Failed to parse profile LLM JSON")
        return {}


def _profile_url_for(prof: dict) -> Optional[str]:
    url = (prof.get("homepage") or prof.get("url") or "").strip()
    return url or None


def enrich_profiles_for_batch(
    professors: list[dict],
    *,
    delay: float = 2.0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    page_base_url: Optional[str] = None,
    send_progress: Optional[Callable[[str], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
) -> list[dict]:
    """Visit each professor profile URL and merge extracted fields into dicts."""
    with_urls = [(i, p) for i, p in enumerate(professors) if _profile_url_for(p)]
    total = len(with_urls)

    for n, (_idx, prof) in enumerate(with_urls, start=1):
        if cancel_checker and cancel_checker():
            break

        profile_url = _profile_url_for(prof)
        if not profile_url:
            continue
        if page_base_url:
            profile_url = resolve_absolute_url(profile_url, page_base_url)
            prof["homepage"] = profile_url

        prof_name = prof.get("name", "")
        if send_progress:
            send_progress(f"正在爬取个人主页 ({n}/{total}): {prof_name}")

        try:
            extracted = extract_professor_profile(
                profile_url,
                name=prof_name,
                affiliation=prof.get("affiliation") or "",
                api_key=api_key,
                base_url=base_url,
                model=model,
                page_base_url=page_base_url,
                cancel_checker=cancel_checker,
            )
            if extracted:
                merge_profile_into_dict(prof, extracted)
                if page_base_url:
                    normalize_school_crawl_professor(prof, page_base_url)
        except Exception as exc:
            logger.warning(
                "Profile enrichment failed for %s (%s): %s",
                prof_name,
                profile_url,
                exc,
            )

        if delay > 0 and n < total:
            time.sleep(delay)

    return professors
