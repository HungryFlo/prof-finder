"""Letter generation using LLM (DeepSeek API)."""

from typing import Optional, Union
from openai import OpenAI

from ..config import settings
from ..models import UserProfile, Professor


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

    SYSTEM_PROMPT_ZH = """你是一位学术联络邮件写作专家。你的任务是帮助学生撰写给潜在导师的学术联络邮件。

邮件应该：
1. 简洁专业，300-500字左右
2. 展示对教授研究的了解（引用具体论文或研究方向）
3. 突出学生的相关背景和匹配点
4. 表达真诚的研究兴趣
5. 语气礼貌正式但不卑微
6. 避免模板化和套话

请直接输出邮件正文，不需要添加任何解释或前言。"""

    SYSTEM_PROMPT_EN = """You are an expert in academic outreach emails. Your task is to help a student draft an email to a prospective supervisor.

The email should:
1. Be concise and professional, roughly 300–500 words (or a proportional length in English)
2. Show understanding of the professor's work (cite specific papers or research directions when relevant)
3. Highlight the student's background and fit
4. Express genuine research interest
5. Use a polite, formal tone without sounding obsequious
6. Avoid boilerplate and clichés

Output only the email body, with no preamble or explanation."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the letter generator.

        Args:
            api_key: DeepSeek API key. Falls back to settings if not provided.
            base_url: API base URL. Falls back to settings if not provided.
        """
        actual_api_key = api_key or settings.deepseek_api_key
        actual_base_url = base_url or settings.deepseek_base_url

        if not actual_api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured")

        self.client = OpenAI(
            api_key=actual_api_key,
            base_url=actual_base_url,
        )

    def generate(
        self,
        profile: Union[UserProfile, dict],
        professor: Union[Professor, dict],
        match_reasons: Optional[list[str]] = None,
        language: str = "en",
    ) -> str:
        """Generate a contact letter.

        Args:
            profile: User profile with background information (object or dict).
            professor: Professor to contact (object or dict).
            match_reasons: Optional list of matching reasons.
            language: "zh" for Chinese, "en" for English.

        Returns:
            Generated letter content.
        """
        lang = language if language in ("zh", "en") else "en"
        student_info = self._format_student_info(profile, lang)
        professor_info = self._format_professor_info(professor, lang)

        if lang == "zh":
            system_prompt = self.SYSTEM_PROMPT_ZH
            lang_instruction = "请用中文撰写邮件。"
            no_reasons = "无特定匹配信息"
            user_prompt = f"""请为以下学生撰写一封给导师的学术联络邮件。

## 学生背景
{student_info}

## 目标导师信息
{professor_info}

## 匹配亮点
{chr(10).join(f'- {r}' for r in (match_reasons or [])) if match_reasons else no_reasons}

{lang_instruction}

请撰写邮件："""
        else:
            system_prompt = self.SYSTEM_PROMPT_EN
            lang_instruction = "Write the email in English."
            no_reasons = "No specific match highlights provided."
            user_prompt = f"""Draft an academic outreach email from the student below to the professor described.

## Student background
{student_info}

## Professor
{professor_info}

## Match highlights
{chr(10).join(f'- {r}' for r in (match_reasons or [])) if match_reasons else no_reasons}

{lang_instruction}

Write the email:"""

        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    def _format_student_info(self, profile: Union[UserProfile, dict], language: str) -> str:
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

        return "\n\n".join(parts) if parts else none_detail

    def _format_professor_info(self, professor: Union[Professor, dict], language: str) -> str:
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
