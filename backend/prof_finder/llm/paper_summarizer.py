"""Paper summarization via LLM with deterministic fallback."""

from __future__ import annotations

import json
from typing import Optional

from ..ai_workflows.provider import LLMProvider
from ..prompts import get_prompt


def _language_params(language: str) -> dict:
    """Return language-dependent prompt variables for paper summarizer."""
    if language == "en":
        return {
            "language_summary_format": "150-300 word English summary focusing on problem, method, results",
            "language_summary_rule": "summary MUST be in English, concise and accurate, no more than 300 words",
        }
    return {
        "language_summary_format": "150-300字的中文摘要，聚焦问题、方法、结果",
        "language_summary_rule": "summary 必须是中文，简洁准确，不超过 300 字",
    }


class PaperSummarizer:
    """Summarize paper text into summary + keywords."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
    ):
        self.provider = provider or LLMProvider(api_key=api_key, base_url=base_url)

    @property
    def enabled(self) -> bool:
        return self.provider.enabled

    def summarize_with_fallback(self, source_type: str, title: str, content: str, language: str = "en") -> dict:
        """Try LLM summary first; fallback to heuristic summary when unavailable."""
        if self.provider.enabled:
            try:
                return self._summarize_by_llm(source_type=source_type, title=title, content=content, language=language)
            except Exception:
                pass

        summary = self._heuristic_summary(content, max_chars=500)
        return {
            "summary": summary,
            "keywords": self._extract_keywords(content)[:12],
        }

    def _summarize_by_llm(self, source_type: str, title: str, content: str, language: str = "en") -> dict:
        """Generate summary using managed prompt templates."""
        clipped = (content or "").strip()
        if len(clipped) > 12000:
            clipped = clipped[:12000]

        lang_params = _language_params(language)
        system_prompt = get_prompt("paper_summarizer", "paper_summary_extraction", "system", **lang_params)
        user_prompt = get_prompt(
            "paper_summarizer",
            "paper_summary_extraction",
            "user",
            source_type=source_type,
            title=title or "Untitled Paper",
            content=clipped or "（无可用正文）",
            **lang_params,
        )

        content_text = self.provider.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        payload = self._safe_parse_json(content_text)
        summary = str(payload.get("summary") or "").strip()
        keywords_raw = payload.get("keywords") or []
        if not isinstance(keywords_raw, list):
            keywords_raw = []
        keywords = [str(item).strip() for item in keywords_raw if str(item).strip()]

        if not summary:
            summary = self._heuristic_summary(content, max_chars=500)
        if not keywords:
            keywords = self._extract_keywords(content)[:12]
        return {"summary": summary, "keywords": keywords[:12]}

    @staticmethod
    def _safe_parse_json(raw: str) -> dict:
        """Parse raw model output into JSON object robustly."""
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(raw[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}

    @staticmethod
    def _heuristic_summary(text: str, max_chars: int = 500) -> str:
        cleaned_lines = []
        for raw in text.splitlines():
            line = raw.strip().lstrip("#").strip()
            if not line:
                continue
            if line.startswith("![]("):
                continue
            cleaned_lines.append(line)
        joined = " ".join(cleaned_lines)
        if len(joined) <= max_chars:
            return joined
        return joined[: max_chars - 1].rstrip() + "…"

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        tech_terms = [
            "machine learning",
            "deep learning",
            "nlp",
            "natural language",
            "computer vision",
            "language model",
            "llm",
            "transformer",
            "bert",
            "gpt",
            "recommendation",
            "knowledge graph",
            "data mining",
            "optimization",
            "security",
            "robotics",
            "reinforcement learning",
        ]
        lower = text.lower()
        found = []
        for term in tech_terms:
            if term in lower:
                found.append(term)
        return found
