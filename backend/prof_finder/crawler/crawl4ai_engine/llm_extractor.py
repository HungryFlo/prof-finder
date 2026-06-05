"""LLM-based professor extraction using crawl4ai + DeepSeek.

Crawls a professor list page to HTML/markdown, then uses an LLM to extract
structured professor data.  This is the flexible fallback for pages where
CSS selectors are impractical.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Callable, Optional
from urllib.parse import urljoin

from .engine import crawl_url_full
from .url_utils import resolve_absolute_url

logger = logging.getLogger(__name__)

# Max characters of page content to send to LLM
_MAX_CONTENT_CHARS = 200000

# LLM retry configuration
_LLM_MAX_RETRIES = 3
_LLM_RETRY_BASE_DELAY = 2.0  # seconds, doubles each retry


def extract_professors_llm(
    url: str,
    affiliation: str = "",
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    send_progress: Optional[Callable[[str], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
) -> list[dict]:
    """Extract professors from a page using LLM analysis.

    Crawls the page with auto_tab_click enabled (for AJAX-loaded content),
    then sends the structured HTML to the configured LLM for extraction.

    Args:
        url: Professor list page URL.
        affiliation: Default affiliation for extracted professors.
        api_key: DeepSeek API key. If None, uses app settings.
        base_url: DeepSeek base URL. If None, uses app settings.
        model: LLM model name. If None, uses app settings or "deepseek-chat".
        send_progress: Optional callback for progress messages.
        cancel_checker: Optional callback that returns True to abort.

    Returns:
        List of professor dicts with keys: name, affiliation, url, email,
        research_interests.
    """
    if cancel_checker and cancel_checker():
        return []

    # Step 1: Crawl the page with auto_tab_click for dynamic content
    if send_progress:
        send_progress("正在爬取页面内容（含动态加载）...")

    crawl_result = crawl_url_full(url, auto_tab_click=True)
    if not crawl_result.success:
        logger.warning("Failed to crawl %s", url)
        return []

    if cancel_checker and cancel_checker():
        return []

    # Step 1.5: Try AJAX auto-detection — always check if the page references
    # AJAX endpoints that might contain professor data.
    ajax_html = _try_ajax_endpoints(url, crawl_result.html or "")
    if ajax_html and len(ajax_html) > len(crawl_result.html or "") * 0.5:
        # AJAX returned substantial content — use it directly
        crawl_result.html = ajax_html

    # Step 2: Choose the best content for extraction
    # If AJAX content is available and large, use it directly (cleaned)
    if ajax_html and len(ajax_html) > 1000:
        content = _clean_html_for_llm(ajax_html)
    else:
        content = _choose_best_content(crawl_result.html, crawl_result.markdown)

    if not content:
        logger.warning("No content extracted from %s", url)
        return []

    # Step 3: Send to LLM for extraction
    if send_progress:
        send_progress("正在使用 AI 分析页面内容...")

    professors = _llm_extract(
        content,
        affiliation,
        api_key=api_key,
        base_url=base_url,
        model=model,
        llm_provider=llm_provider,
    )

    for prof in professors:
        for key in ("url", "homepage"):
            value = prof.get(key)
            if value and isinstance(value, str):
                prof[key] = resolve_absolute_url(value, url)

    if send_progress:
        send_progress(f"AI 提取完成，共识别 {len(professors)} 位教授")

    return professors


def _choose_best_content(html: str, markdown: str) -> str:
    """Choose the best content format for LLM extraction.

    Prefers HTML when it has structured professor-related elements,
    otherwise falls back to markdown.
    """
    if not html and not markdown:
        return ""

    # Check if HTML has structured professor data
    if html:
        # Look for common professor-related patterns in HTML
        has_professor_data = any(pattern in html for pattern in [
            'teacher', 'faculty', 'professor', 'staff', 'member',
            '教授', '教师', '师资', '研究员', 'staff_name',
            'news_title', 'person_name', 'member_name',
        ])
        if has_professor_data:
            # Use HTML but clean it up for the LLM
            return _clean_html_for_llm(html)

    # Fall back to markdown
    return markdown[:_MAX_CONTENT_CHARS]


def _clean_html_for_llm(html: str) -> str:
    """Clean HTML for LLM consumption — remove noise, keep structure."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, nav, footer
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Try to find the main content area
    # NOTE: avoid overly broad matches like "body" — they match <body> and
    # effectively disable filtering.
    main_content = (
        soup.find("div", class_=re.compile(r"teacher|faculty|staff|faculty-list|teacher-list", re.I))
        or soup.find("main")
        or soup.find("article")
        or soup.body
    )

    if main_content:
        text = str(main_content)
    else:
        text = str(soup)

    # Truncate if too long — try to cut at a tag boundary
    if len(text) > _MAX_CONTENT_CHARS:
        text = text[:_MAX_CONTENT_CHARS]
        # Try to cut at the last complete closing tag to avoid broken HTML
        last_close = text.rfind(">")
        if last_close > _MAX_CONTENT_CHARS * 0.9:
            text = text[: last_close + 1]

    return text


def _llm_extract(
    content: str,
    affiliation: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    llm_provider: Optional[str] = None,
) -> list[dict]:
    """Use LLM to extract professor data from page content."""
    from ...ai_workflows.provider import LLMProvider
    from ...config import settings as app_settings
    from ...llm.config import LLMConfig, resolve_llm_config

    if api_key or base_url or model or llm_provider:
        resolved = resolve_llm_config(app_settings=app_settings)
        config = LLMConfig(
            provider=llm_provider or resolved.provider,
            api_key=api_key or resolved.api_key,
            base_url=base_url or resolved.base_url,
            model=model or resolved.model,
        )
    else:
        config = resolve_llm_config(app_settings=app_settings)

    provider = LLMProvider(config=config)
    if not provider.enabled:
        logger.error("No LLM API key/model configured for LLM extraction")
        return []

    truncated = content[:_MAX_CONTENT_CHARS]

    prompt = f"""从以下网页 HTML 中提取所有教授/教师的信息，返回 JSON 数组。
默认机构：{affiliation if affiliation else "未知"}
JSON 格式：[{{"name":"姓名","affiliation":"机构","url":"链接或null","email":"邮箱或null","homepage":"主页或null","research_interests":[]}}]
只输出 JSON 数组，无其他文字。注意提取中文姓名（2-4字）。

示例：
输入 HTML 片段：
<div class="teacher-card">
  <h3><a href="/teacher/zhangsan">张三</a></h3>
  <p>教授 · zhangsan@example.edu.cn</p>
  <p>研究方向：机器学习、自然语言处理</p>
</div>
<div class="teacher-card">
  <h3>李四</h3>
  <p>副教授</p>
</div>

输出：
[{{"name":"张三","affiliation":"默认机构","url":"/teacher/zhangsan","email":"zhangsan@example.edu.cn","homepage":null,"research_interests":["机器学习","自然语言处理"]}},{{"name":"李四","affiliation":"默认机构","url":null,"email":null,"homepage":null,"research_interests":[]}}]

注意：
- 如果页面是表格形式，逐行提取每一行的教师信息。
- 如果姓名和职称在同一元素中（如"张三 教授"），拆分后分别填入对应字段。
- research_interests 应为字符串数组，如果无法提取则为空数组 []。
- url / homepage 可以是相对路径（如 /cris/rp/xxx），按 HTML 中的 href 原样填写即可。

HTML 内容：
{truncated}
"""

    try:
        content_text = provider.chat_completion(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=65536,
        )
        professors = _parse_llm_response(content_text)
        for prof in professors:
            if not prof.get("affiliation"):
                prof["affiliation"] = affiliation
            if not isinstance(prof.get("research_interests"), list):
                prof["research_interests"] = []
        return [p for p in professors if p.get("name")]
    except Exception as exc:
        error_msg = str(exc)
        if "401" in error_msg or "authentication" in error_msg.lower():
            logger.error("LLM extraction failed: API key 无效，请在设置中检查 LLM API Key")
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            logger.error("LLM extraction failed: 请求超时，请检查网络连接或稍后重试")
        else:
            logger.exception("LLM extraction failed")
        return []


def _parse_llm_response(content: str) -> list[dict]:
    """Parse JSON array from LLM response, handling common formatting issues."""
    content = content.strip()

    # Try to find JSON array in the response
    # Remove markdown code fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        # Skip first line (```json or ```)
        lines = lines[1:]
        # Remove trailing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    # Find the first [ and last ]
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.warning("No JSON array found in LLM response")
        return []

    json_str = content[start : end + 1]

    try:
        result = json.loads(json_str)
        if isinstance(result, list):
            return result
        logger.warning("LLM response parsed but is not a list")
        return []
    except json.JSONDecodeError:
        # Try to fix common LLM JSON errors: trailing commas
        try:
            fixed = re.sub(r",\s*([}\]])", r"\1", json_str)
            result = json.loads(fixed)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        logger.warning("Failed to parse LLM JSON response")
        return []


# ---------------------------------------------------------------------------
# AJAX auto-detection helpers
# ---------------------------------------------------------------------------

# Patterns that suggest professor/faculty data in a page
_PROFESSOR_KEYWORDS = [
    "教授", "副教授", "讲师", "研究员", "助理教授", "教师", "师资",
    "professor", "faculty", "teacher", "staff",
]


def _has_no_professor_data(html: str) -> bool:
    """Check if HTML has no professor-related content."""
    if not html:
        return True
    html_lower = html.lower()
    return not any(kw in html_lower for kw in _PROFESSOR_KEYWORDS)


def _extract_balanced_braces(text: str, start_pos: int) -> Optional[str]:
    """Extract a balanced {...} block starting at the given position.

    Returns the content between the outermost braces (exclusive), or None
    if no balanced block is found.
    """
    if start_pos >= len(text) or text[start_pos] != "{":
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start_pos, len(text)):
        ch = text[i]

        if escape_next:
            escape_next = False
            continue

        if ch == "\\":
            escape_next = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                # Return content between { and }
                return text[start_pos + 1 : i]

    return None


def _try_ajax_endpoints(page_url: str, html: str) -> str:
    """Detect AJAX endpoints in page HTML and try to fetch data.

    Looks for common patterns like:
    - $.ajax({url: '...'}) calls (with variable resolution)
    - fetch('...') calls
    - XMLHttpRequest.open() calls

    Then tries to call those endpoints with inferred parameters.

    Returns:
        Combined HTML from AJAX responses, or empty string if nothing found.
    """
    import requests as req

    # Step 1: Parse JavaScript variables that might be used as AJAX params
    js_vars = {}
    for match in re.finditer(r'var\s+(\w+)\s*=\s*["\']([^"\']*)["\']\s*;', html):
        js_vars[match.group(1)] = match.group(2)
    for match in re.finditer(r'var\s+(\w+)\s*=\s*(\d+)\s*;', html):
        js_vars[match.group(1)] = match.group(2)

    # Step 2: Find AJAX URLs and their data parameters
    ajax_configs = []  # list of (url, params_dict, method)

    # Pattern 1: jQuery $.ajax — find url and data in the same block
    # Use a broader match: find $.ajax({ and extract url/data/type before the
    # success/error callback functions
    for match in re.finditer(
        r'\$\.\s*ajax\s*\(\s*\{', html
    ):
        # Grab a reasonable chunk after the match to extract config
        start = match.end()
        block = html[start : start + 2000]

        # Extract URL
        url_match = re.search(r'url\s*:\s*["\']([^"\']+)["\']', block)
        if not url_match:
            continue
        ajax_url = url_match.group(1)

        # Extract data parameters — use balanced brace matching for robustness
        # against nested objects
        data_match = re.search(r'data\s*:\s*\{', block)
        params = {}
        if data_match:
            brace_start = data_match.end() - 1  # position of '{'
            data_str = _extract_balanced_braces(block, brace_start)
            if data_str:
                # Parse key:value pairs (handles 'val', "val", and varName)
                for param_match in re.finditer(
                    r"(\w+)\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|(\w+))", data_str
                ):
                    key = param_match.group(1)
                    value = (
                        param_match.group(2)
                        or param_match.group(3)
                        or param_match.group(4)
                        or ""
                    )
                    # Resolve JS variable references
                    if value in js_vars:
                        value = js_vars[value]
                    params[key] = value

        # Extract method
        method_match = re.search(r"type\s*:\s*['\"](\w+)['\"]", block)
        method = method_match.group(1).upper() if method_match else "POST"

        ajax_configs.append((ajax_url, params, method))

    # Pattern 2: fetch()
    for match in re.finditer(r'fetch\s*\(\s*["\']([^"\']+)["\']', html):
        ajax_configs.append((match.group(1), {}, "GET"))

    # Pattern 3: XMLHttpRequest.open
    for match in re.finditer(
        r'\.open\s*\(\s*["\']([A-Z]+)["\']\s*,\s*["\']([^"\']+)["\']', html
    ):
        ajax_configs.append((match.group(2), {}, match.group(1)))

    if not ajax_configs:
        return ""

    logger.info("Found %d potential AJAX endpoints, trying...", len(ajax_configs))

    session = req.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    })

    # Visit the page first to get cookies
    try:
        session.get(page_url, timeout=15)
    except Exception:
        pass

    collected_html = ""

    for ajax_url, params, method in ajax_configs:
        # Resolve relative URLs
        if not ajax_url.startswith("http"):
            ajax_url = urljoin(page_url, ajax_url)

        try:
            headers = {
                "Referer": page_url,
                "X-Requested-With": "XMLHttpRequest",
            }

            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                resp = session.post(
                    ajax_url,
                    data=params,
                    headers=headers,
                    timeout=15,
                )
            else:
                resp = session.get(ajax_url, params=params, headers=headers, timeout=15)

            if resp.status_code == 200 and len(resp.text) > 100:
                # Try to parse as JSON and extract content field
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        # Look for HTML content in common field names
                        for field in ["content", "html", "data", "list", "items"]:
                            if field in data and isinstance(data[field], str) and len(data[field]) > 100:
                                collected_html += data[field]
                                logger.info("Got %d chars from AJAX field '%s'", len(data[field]), field)
                                break
                except (json.JSONDecodeError, ValueError):
                    # Not JSON, use raw text if it looks like HTML
                    if "<" in resp.text and ">" in resp.text:
                        collected_html += resp.text
                        logger.info("Got %d chars raw HTML from AJAX", len(resp.text))

        except Exception:
            continue

    return collected_html
