"""Professor research profile generation via LLM."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from openai import OpenAI

from ..config import settings
from ..prompts import get_prompt

logger = logging.getLogger(__name__)


class ProfessorProfileGenerator:
    """Generate evidence-aware research profiles from professor data."""

    MAX_ANALYZE_RETRIES = 2

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        actual_api_key = api_key or settings.deepseek_api_key
        actual_base_url = base_url or settings.deepseek_base_url
        self.enabled = bool(
            actual_api_key and actual_api_key not in {"test_key", "your_api_key_here"}
        )
        self.client: Optional[OpenAI] = None
        if self.enabled:
            self.client = OpenAI(api_key=actual_api_key, base_url=actual_base_url)

    def generate(self, professor_data: dict) -> dict:
        """Run analyzer and builder prompts for a professor research profile."""
        if not self.enabled or self.client is None:
            raise ValueError("请先配置 DeepSeek API Key 后再生成教授画像")

        source_bundle = self._build_source_bundle(professor_data)
        analysis = self._analyze(source_bundle)
        research_profile = self._build_profile(analysis)
        return {
            "research_profile": research_profile,
            "research_profile_analysis": analysis,
            "research_profile_sources": source_bundle["source_meta"],
            "research_profile_evidence": self._as_list(analysis.get("evidence_notes")),
            "research_profile_conflicts": self._as_list(analysis.get("conflict_notes")),
        }

    def _build_source_bundle(self, professor_data: dict) -> dict:
        """Assemble professor fields into a source bundle for the analyzer."""
        manual_notes = (professor_data.get("manual_notes") or "").strip()
        research_interests = professor_data.get("research_interests") or []
        publications = professor_data.get("publications") or []
        paper_summaries = professor_data.get("paper_summaries") or []
        affiliation = professor_data.get("affiliation") or ""
        homepage = professor_data.get("homepage") or ""
        google_scholar_url = professor_data.get("google_scholar_url") or ""

        source_meta: list[dict] = []
        evidence_fields: dict[str, str] = {}

        if research_interests:
            source_meta.append({"field": "research_interests", "count": len(research_interests)})
            evidence_fields["research_interests"] = "; ".join(research_interests)
        if publications:
            source_meta.append({"field": "publications", "count": len(publications)})
        if paper_summaries:
            source_meta.append({"field": "paper_summaries", "count": len(paper_summaries)})
        if manual_notes:
            source_meta.append({"field": "manual_notes", "char_count": len(manual_notes)})

        source_info_lines = [f"所属机构: {affiliation}"]
        if homepage:
            source_info_lines.append(f"个人主页: {homepage}")
        if google_scholar_url:
            source_info_lines.append(f"Google Scholar: {google_scholar_url}")
        source_info = "\n".join(source_info_lines)

        return {
            "manual_notes": manual_notes or "(无)",
            "research_interests": "; ".join(research_interests) if research_interests else "(无)",
            "publications": self._format_publications(publications),
            "paper_summaries": self._format_paper_summaries(paper_summaries),
            "source_info": source_info,
            "source_meta": source_meta,
        }

    @staticmethod
    def _format_publications(publications: list) -> str:
        if not publications:
            return "(无)"
        lines = []
        for idx, pub in enumerate(publications[:30], start=1):
            title = pub.get("title", "")
            year = pub.get("year", "")
            citations = pub.get("citations")
            parts = [f"{idx}. {title}"]
            if year:
                parts.append(f"({year})")
            if citations is not None:
                parts.append(f"-- 引用: {citations}")
            lines.append(" ".join(parts))
        return "\n".join(lines)

    @staticmethod
    def _format_paper_summaries(paper_summaries: list) -> str:
        if not paper_summaries:
            return "(无)"
        blocks = []
        for idx, item in enumerate(paper_summaries[:20], start=1):
            title = item.get("title", "")
            summary = item.get("summary", "")
            keywords = item.get("keywords") or []
            parts = [f"### {idx}. {title}"]
            if keywords:
                parts.append(f"关键词: {', '.join(keywords)}")
            if summary:
                parts.append(summary)
            blocks.append("\n".join(parts))
        return "\n\n".join(blocks)

    def _analyze(self, source_bundle: dict) -> dict:
        """Generate structured professor research analysis JSON."""
        assert self.client is not None
        system_prompt = get_prompt("professor_profile", "material_analysis", "system")
        user_prompt = get_prompt(
            "professor_profile",
            "material_analysis",
            "user",
            manual_notes=source_bundle["manual_notes"],
            research_interests=source_bundle["research_interests"],
            publications=source_bundle["publications"],
            paper_summaries=source_bundle["paper_summaries"],
            source_info=source_bundle["source_info"],
        )

        last_error: Optional[Exception] = None
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        for attempt in range(self.MAX_ANALYZE_RETRIES + 1):
            response = self.client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=messages,
                temperature=0.2,
            )
            raw = (response.choices[0].message.content or "").strip()
            payload = self._parse_analysis_json(raw)
            if payload:
                return payload
            last_error = ValueError("教授画像分析结果不是有效 JSON")
            logger.warning(
                "Professor profile analyzer returned non-JSON (attempt %s), raw prefix: %s",
                attempt + 1,
                raw[:300],
            )
            if attempt < self.MAX_ANALYZE_RETRIES:
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "上一条回复不是合法 JSON（例如尾随逗号、未转义引号或夹杂解释文字）。"
                            "请只输出一个 JSON 对象，不要 markdown 代码块，不要前言后记。"
                        ),
                    }
                )
        raise ValueError(f"教授画像分析失败：{last_error}")

    def _build_profile(self, analysis: dict) -> str:
        """Generate the readable Markdown research profile."""
        assert self.client is not None
        system_prompt = get_prompt("professor_profile", "profile_builder", "system")
        user_prompt = get_prompt(
            "professor_profile",
            "profile_builder",
            "user",
            analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
        )
        for attempt in range(self.MAX_ANALYZE_RETRIES + 1):
            response = self.client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content
            logger.warning("Professor profile builder returned empty (attempt %s)", attempt + 1)
        raise ValueError("教授画像生成结果为空")

    @classmethod
    def _parse_analysis_json(cls, raw: str) -> dict:
        text = (raw or "").strip()
        if not text:
            return {}

        for candidate in cls._json_candidates(text):
            for patched in (candidate, cls._fix_trailing_commas(candidate)):
                try:
                    parsed = json.loads(patched)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue
        return {}

    @staticmethod
    def _json_candidates(text: str) -> list[str]:
        out: list[str] = []
        if text:
            out.append(text)

        fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
        if fence:
            out.append(fence.group(1).strip())

        balanced = ProfessorProfileGenerator._first_balanced_json_object(text)
        if balanced:
            out.append(balanced)

        return [c for c in out if c]

    @staticmethod
    def _first_balanced_json_object(text: str) -> Optional[str]:
        start = text.find("{")
        if start < 0:
            return None
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
        return None

    @staticmethod
    def _fix_trailing_commas(s: str) -> str:
        return re.sub(r",\s*([}\]])", r"\1", s)

    @staticmethod
    def _as_list(value) -> list:
        if isinstance(value, list):
            return value
        if value:
            return [str(value)]
        return []
