"""Student academic profile generation via LLM."""

from __future__ import annotations

import json
import logging
import re
from typing import Generator, Optional

from ..ai_workflows.provider import LLMProvider
from ..prompts import get_prompt

logger = logging.getLogger(__name__)


def _language_instruction(language: str) -> str:
    """Return a language instruction string for LLM prompt injection."""
    if language == "en":
        return "English（英文）"
    return "中文（Chinese）"


class StudentProfileGenerator:
    """Generate evidence-aware academic profiles from student materials."""

    MAX_ANALYZE_RETRIES = 2

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

    def generate(
        self,
        materials: list[dict],
        manual_inputs: dict,
        previous_academic_profile: str = "",
        previous_profile_analysis: dict | None = None,
        language: str = "en",
    ) -> dict:
        """Run analyzer and builder prompts for a student profile."""
        if not self.provider.enabled:
            raise ValueError("请先配置 DeepSeek API Key 后再生成学生画像")

        analysis = self._analyze(
            materials=materials,
            manual_inputs=manual_inputs,
            previous_academic_profile=previous_academic_profile,
            previous_profile_analysis=previous_profile_analysis,
            language=language,
        )
        academic_profile = self._build_profile(analysis=analysis, language=language)
        return {
            "academic_profile": academic_profile,
            "profile_analysis": analysis,
            "evidence_notes": self._as_list(analysis.get("evidence_notes")),
            "conflict_notes": self._as_list(analysis.get("conflict_notes")),
        }

    def interview(
        self,
        profile_analysis: dict,
        academic_profile: str,
        history: list[dict],
        message: str,
        locale: str = "zh",
    ) -> str:
        """Generate the next AI interviewer response based on profile gaps and chat history.

        Args:
            profile_analysis: Current structured profile analysis JSON.
            academic_profile: Current readable Markdown profile.
            history: Chat history as [{role: "user"|"assistant", content: str}].
            message: Latest message from the student.
            locale: UI locale ("zh" or "en") for reply language.

        Returns:
            AI interviewer reply string.
        """
        if not self.provider.enabled:
            raise ValueError("请先配置 DeepSeek API Key")

        lang = "en" if locale == "en" else "zh"
        lang_instr = _language_instruction(lang)
        optimize_hint = '"Optimize Profile"' if lang == "en" else "「优化画像」"
        empty_profile = "(Not generated yet)" if lang == "en" else "（尚未生成）"

        system_prompt = get_prompt(
            "student_profile",
            "profile_interviewer",
            "system",
            language_instruction=lang_instr,
            optimize_button_hint=optimize_hint,
        )
        history_text = self._format_chat_history(history, message, locale=lang)

        user_prompt = get_prompt(
            "student_profile",
            "profile_interviewer",
            "user",
            profile_analysis=json.dumps(profile_analysis, ensure_ascii=False, indent=2),
            academic_profile=academic_profile or empty_profile,
            history_text=history_text,
        )

        return self.provider.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )

    def interview_stream(
        self,
        profile_analysis: dict,
        academic_profile: str,
        history: list[dict],
        message: str,
        locale: str = "zh",
    ) -> Generator[str, None, None]:
        """Streaming variant of interview(): yields content tokens.

        Same prompt logic as interview() but streams tokens as they arrive.
        """
        if not self.provider.enabled:
            raise ValueError("请先配置 DeepSeek API Key")

        lang = "en" if locale == "en" else "zh"
        lang_instr = _language_instruction(lang)
        optimize_hint = '"Optimize Profile"' if lang == "en" else "「优化画像」"
        empty_profile = "(Not generated yet)" if lang == "en" else "（尚未生成）"

        system_prompt = get_prompt(
            "student_profile",
            "profile_interviewer",
            "system",
            language_instruction=lang_instr,
            optimize_button_hint=optimize_hint,
        )
        history_text = self._format_chat_history(history, message, locale=lang)

        user_prompt = get_prompt(
            "student_profile",
            "profile_interviewer",
            "user",
            profile_analysis=json.dumps(profile_analysis, ensure_ascii=False, indent=2),
            academic_profile=academic_profile or empty_profile,
            history_text=history_text,
        )

        yield from self.provider.chat_completion_stream(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )

    def refine_from_chat(
        self,
        materials: list[dict],
        manual_inputs: dict,
        chat_history: list[dict],
        academic_profile: str = "",
        profile_analysis: dict | None = None,
        language: str = "en",
    ) -> dict:
        """Regenerate profile incorporating insights from chat Q&A.

        Enriches manual_inputs with a summary of the chat conversation, then
        re-runs the full two-stage generate pipeline.

        Args:
            materials: Original profile materials.
            manual_inputs: Original manual inputs dict.
            chat_history: Full chat history [{role, content}].
            academic_profile: Current readable Markdown profile (for incremental update).
            profile_analysis: Current structured analysis JSON (for incremental update).
            language: Output language ("zh" or "en").

        Returns:
            Same dict as generate(): academic_profile, profile_analysis, etc.
        """
        chat_summary = self._build_chat_summary(chat_history)
        enriched = dict(manual_inputs)
        enriched["_chat_refinement"] = chat_summary
        return self.generate(
            materials=materials,
            manual_inputs=enriched,
            previous_academic_profile=academic_profile,
            previous_profile_analysis=profile_analysis,
            language=language,
        )

    @staticmethod
    def _format_chat_history(
        history: list[dict], latest_message: str, *, locale: str = "zh"
    ) -> str:
        """Format chat history for prompt injection."""
        if locale == "en":
            user_label, assistant_label = "Student", "AI"
            empty = "(No conversation yet; proactively ask the first question.)"
        else:
            user_label, assistant_label = "学生", "AI"
            empty = "（尚无对话历史，请主动提出第一个问题）"
        lines: list[str] = []
        for msg in history:
            role_label = user_label if msg.get("role") == "user" else assistant_label
            content = (msg.get("content") or "").strip()
            if content:
                lines.append(f"{role_label}: {content}")
        if latest_message.strip():
            lines.append(f"{user_label}: {latest_message.strip()}")
        return "\n".join(lines) if lines else empty

    @staticmethod
    def _build_chat_summary(history: list[dict]) -> str:
        """Convert chat history into a structured summary for the analyzer."""
        lines = ["以下信息来自学生与 AI 访谈助手的对话：", ""]
        for msg in history:
            if not msg.get("content"):
                continue
            role_label = "学生" if msg.get("role") == "user" else "AI 提问"
            lines.append(f"**{role_label}**: {msg['content'].strip()}")
            lines.append("")
        return "\n".join(lines).strip()

    def _analyze(
        self,
        materials: list[dict],
        manual_inputs: dict,
        previous_academic_profile: str = "",
        previous_profile_analysis: dict | None = None,
        language: str = "en",
    ) -> dict:
        """Generate structured profile analysis JSON."""
        lang_instr = _language_instruction(language)
        system_prompt = get_prompt(
            "student_profile", "material_analysis", "system",
            language_instruction=lang_instr,
        )
        base_user = get_prompt(
            "student_profile",
            "material_analysis",
            "user",
            manual_inputs=json.dumps(manual_inputs, ensure_ascii=False, indent=2),
            materials=self._format_materials(materials),
            previous_academic_profile=previous_academic_profile or "（无）",
            previous_profile_analysis=(
                json.dumps(previous_profile_analysis, ensure_ascii=False, indent=2)
                if previous_profile_analysis
                else "（无）"
            ),
        )

        last_error: Optional[Exception] = None
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": base_user},
        ]
        for attempt in range(self.MAX_ANALYZE_RETRIES + 1):
            raw = self.provider.chat_completion(
                messages=messages,
                temperature=0.2,
            )
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

    def _build_profile(self, analysis: dict, language: str = "en") -> str:
        """Generate the readable Markdown academic profile."""
        lang_instr = _language_instruction(language)
        system_prompt = get_prompt(
            "student_profile", "profile_builder", "system",
            language_instruction=lang_instr,
        )
        user_prompt = get_prompt(
            "student_profile",
            "profile_builder",
            "user",
            analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
        )
        for attempt in range(self.MAX_ANALYZE_RETRIES + 1):
            content = self.provider.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
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
