"""Letter generation using LLM (DeepSeek API)."""

from typing import Callable, Optional, Union

from ..ai_workflows.provider import LLMProvider
from ..prompts import get_prompt


def _get_attr(obj: Union[dict, object], key: str, default=None):
    """Get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _resolved_name(entity: Union[dict, object], language: str) -> str:
    """Name for salutation in the chosen letter language; falls back to `name`."""
    nl = _get_attr(entity, "name_locales")
    if isinstance(nl, dict):
        v = nl.get(language)
        if v is not None and str(v).strip():
            return str(v).strip()
    n = _get_attr(entity, "name")
    return str(n).strip() if n else ""


class LetterGenerator:
    """Generate academic contact letters using LLM."""

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
        profile: Union[dict, object],
        professor: Union[dict, object],
        match_reasons: Optional[list[str]] = None,
        language: str = "en",
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> str:
        """Generate a contact letter.

        Args:
            profile: User profile with background information (object or dict).
            professor: Professor to contact (object or dict).
            match_reasons: Optional list of matching reasons.
            language: "zh" for Chinese, "en" for English.
            cancel_checker: If given, allows the LLM call to be aborted mid-stream.

        Returns:
            Generated letter content.
        """
        lang = language if language in ("zh", "en") else "en"
        student_info = self._format_student_info(profile, lang)
        professor_info = self._format_professor_info(professor, lang)
        prompt_name = f"generate_letter_{lang}"

        if lang == "zh":
            lang_instruction = "请用中文撰写邮件。"
            no_reasons = "无特定匹配信息"
        else:
            lang_instruction = "Write the email in English."
            no_reasons = "No specific match highlights provided."

        match_text = "\n".join(f"- {r}" for r in (match_reasons or [])) if match_reasons else no_reasons
        system_prompt = get_prompt("letter", prompt_name, "system")
        user_prompt = get_prompt(
            "letter",
            prompt_name,
            "user",
            student_info=student_info,
            professor_info=professor_info,
            match_reasons=match_text,
            language_instruction=lang_instruction,
        )

        return self.provider.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            cancel_checker=cancel_checker,
        )

    def _format_student_info(self, profile: Union[dict, object], language: str) -> str:
        """Format student profile for the prompt."""
        parts = []
        name = _resolved_name(profile, language)
        if language == "zh":
            if name:
                parts.append(f"姓名：{name}")
            unknown = "未知"
            exp_default = "研究经历"
            proj_default = "项目"
            none_detail = "无详细信息"
        else:
            if name:
                parts.append(f"Name: {name}")
            unknown = "n/a"
            exp_default = "Research experience"
            proj_default = "Project"
            none_detail = "No details provided"

        academic_profile = _get_attr(profile, "academic_profile")
        if academic_profile:
            if language == "zh":
                parts.append(f"学生学术画像：\n{str(academic_profile)[:1200]}")
            else:
                parts.append(f"Academic profile (student):\n{str(academic_profile)[:1200]}")

        profile_analysis = _get_attr(profile, "profile_analysis") or {}
        if isinstance(profile_analysis, dict):
            positioning = profile_analysis.get("academic_positioning")
            if positioning:
                label = "学术定位：" if language == "zh" else "Positioning: "
                parts.append(f"{label}{positioning}")

        education = _get_attr(profile, "education") or []
        if education:
            edu_lines = []
            for edu in education:
                line = f"- {edu.get('degree', unknown)}: {edu.get('school', unknown)}"
                if edu.get("major"):
                    line += f" ({edu['major']})"
                edu_lines.append(line)
            header = "教育背景：" if language == "zh" else "Education:\n"
            parts.append(header + "\n".join(edu_lines))

        research_experience = _get_attr(profile, "research_experience") or []
        if research_experience:
            exp_lines = []
            for exp in research_experience:
                line = f"- {exp.get('title', exp_default)}"
                if exp.get("organization"):
                    line += f" @ {exp['organization']}"
                if exp.get("description"):
                    line += f"\n  {exp['description'][:200]}"
                exp_lines.append(line)
            header = "科研经历：" if language == "zh" else "Research experience:\n"
            parts.append(header + "\n".join(exp_lines))

        projects = _get_attr(profile, "projects") or []
        if projects:
            proj_lines = [f"- {p.get('name', proj_default)}" for p in projects]
            header = "项目经历：" if language == "zh" else "Projects:\n"
            parts.append(header + "\n".join(proj_lines))

        skills = _get_attr(profile, "skills") or []
        if skills:
            label = "技能专长：" if language == "zh" else "Skills: "
            parts.append(f"{label}{', '.join(skills)}")

        experience_stories = (_get_attr(profile, "experience_stories") or "").strip()
        if experience_stories:
            label = (
                "信息池细化经历：\n"
                if language == "zh"
                else "Detailed experiences from material pool:\n"
            )
            parts.append(f"{label}{experience_stories}")

        return "\n\n".join(parts) if parts else none_detail

    def _format_professor_info(self, professor: Union[dict, object], language: str) -> str:
        """Format professor info for the prompt."""
        parts = []
        name = _resolved_name(professor, language)
        if language == "zh":
            parts.append(f"姓名：{name}")
        else:
            parts.append(f"Name: {name}")

        affiliation = _get_attr(professor, "affiliation")
        if affiliation:
            parts.append(f"单位：{affiliation}" if language == "zh" else f"Affiliation: {affiliation}")

        research_profile = _get_attr(professor, "research_profile")
        if research_profile:
            label = "教授科研画像：\n" if language == "zh" else "Research profile (professor):\n"
            parts.append(f"{label}{str(research_profile)[:1500]}")

        research_profile_analysis = _get_attr(professor, "research_profile_analysis") or {}
        if isinstance(research_profile_analysis, dict):
            positioning = research_profile_analysis.get("research_positioning")
            if positioning:
                parts.append(
                    f"科研定位：{positioning}"
                    if language == "zh"
                    else f"Research positioning: {positioning}"
                )
            fit_signals = research_profile_analysis.get("student_fit_signals") or []
            if isinstance(fit_signals, list):
                signal_lines = []
                for item in fit_signals:
                    if isinstance(item, dict) and item.get("signal"):
                        signal_lines.append(f"- {item['signal']}")
                    elif isinstance(item, str):
                        signal_lines.append(f"- {item}")
                if signal_lines:
                    header = "学生适配信号：\n" if language == "zh" else "Student fit signals:\n"
                    parts.append(header + "\n".join(signal_lines))

        research_interests = _get_attr(professor, "research_interests") or []
        if research_interests:
            label = "研究方向：" if language == "zh" else "Research interests: "
            parts.append(f"{label}{', '.join(research_interests)}")

        publications = _get_attr(professor, "publications") or []
        if publications:
            pub_lines = []
            for pub in publications[:5]:
                title = pub.get("title", "")
                year = pub.get("year", "")
                if title:
                    pub_lines.append(f"- {title} ({year})")
            if pub_lines:
                header = "代表论文：\n" if language == "zh" else "Selected publications:\n"
                parts.append(header + "\n".join(pub_lines))

        h_index = _get_attr(professor, "h_index")
        if h_index:
            parts.append(f"H-Index：{h_index}" if language == "zh" else f"H-index: {h_index}")

        return "\n".join(parts)
