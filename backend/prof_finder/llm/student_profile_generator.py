"""Student academic profile generation via LLM."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from openai import OpenAI

from ..config import settings
from ..prompts import get_prompt

logger = logging.getLogger(__name__)


class StudentProfileGenerator:
    """Generate evidence-aware academic profiles from student materials."""

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

    def generate(self, materials: list[dict], manual_inputs: dict) -> dict:
        """Run analyzer and builder prompts for a student profile."""
        if not self.enabled or self.client is None:
            raise ValueError("请先配置 DeepSeek API Key 后再生成学生画像")

        analysis = self._analyze(materials=materials, manual_inputs=manual_inputs)
        academic_profile = self._build_profile(analysis=analysis)
        return {
            "academic_profile": academic_profile,
            "profile_analysis": analysis,
            "evidence_notes": self._as_list(analysis.get("evidence_notes")),
            "conflict_notes": self._as_list(analysis.get("conflict_notes")),
        }

    def _analyze(self, materials: list[dict], manual_inputs: dict) -> dict:
        """Generate structured profile analysis JSON."""
        assert self.client is not None
        system_prompt = get_prompt("student_profile", "material_analysis", "system")
        base_user = get_prompt(
            "student_profile",
            "material_analysis",
            "user",
            manual_inputs=json.dumps(manual_inputs, ensure_ascii=False, indent=2),
            materials=self._format_materials(materials),
        )

        last_error: Optional[Exception] = None
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": base_user},
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
            last_error = ValueError("学生画像分析结果不是有效 JSON")
            logger.warning(
                "Student profile analyzer returned non-JSON (attempt %s), raw prefix: %s",
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
        raise ValueError(f"学生画像分析失败：{last_error}")

    def _build_profile(self, analysis: dict) -> str:
        """Generate the readable Markdown academic profile."""
        assert self.client is not None
        system_prompt = get_prompt("student_profile", "profile_builder", "system")
        user_prompt = get_prompt(
            "student_profile",
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
            logger.warning("Student profile builder returned empty (attempt %s)", attempt + 1)
        raise ValueError("学生画像生成结果为空")

    @staticmethod
    def _format_materials(materials: list[dict]) -> str:
        blocks = []
        for idx, material in enumerate(materials, start=1):
            label = material.get("filename") or material.get("field") or f"material-{idx}"
            source_type = material.get("source_type") or "unknown"
            content = (material.get("content") or "").strip()
            blocks.append(f"### {idx}. {label} ({source_type})\n{content}")
        return "\n\n".join(blocks)

    @classmethod
    def _parse_analysis_json(cls, raw: str) -> dict:
        """Parse analyzer output: code fences, balanced `{...}`, trailing-comma fix."""
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
        """Ordered list of substrings that might be valid JSON objects."""
        out: list[str] = []
        if text:
            out.append(text)

        fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
        if fence:
            out.append(fence.group(1).strip())

        balanced = StudentProfileGenerator._first_balanced_json_object(text)
        if balanced:
            out.append(balanced)

        return [c for c in out if c]

    @staticmethod
    def _first_balanced_json_object(text: str) -> Optional[str]:
        """Return substring from first `{` through matching `}`, respecting strings."""
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
        """Remove trailing commas before `}` or `]` (common LLM JSON mistake)."""
        return re.sub(r",\s*([}\]])", r"\1", s)

    @staticmethod
    def _as_list(value) -> list:
        if isinstance(value, list):
            return value
        if value:
            return [str(value)]
        return []
