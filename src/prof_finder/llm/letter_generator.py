"""Letter generation using LLM (DeepSeek API)."""

from typing import Optional
from openai import OpenAI

from ..config import settings
from ..models import UserProfile, Professor


class LetterGenerator:
    """Generate academic contact letters using LLM."""

    SYSTEM_PROMPT = """你是一位学术联络邮件写作专家。你的任务是帮助学生撰写给潜在导师的学术联络邮件。

邮件应该：
1. 简洁专业，300-500字左右
2. 展示对教授研究的了解（引用具体论文或研究方向）
3. 突出学生的相关背景和匹配点
4. 表达真诚的研究兴趣
5. 语气礼貌正式但不卑微
6. 避免模板化和套话

请直接输出邮件正文，不需要添加任何解释或前言。"""

    def __init__(self):
        """Initialize the letter generator."""
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured in .env")

        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    def generate(
        self,
        profile: UserProfile,
        professor: Professor,
        match_reasons: Optional[list[str]] = None,
        language: str = "zh",
    ) -> str:
        """Generate a contact letter.
        
        Args:
            profile: User profile with background information.
            professor: Professor to contact.
            match_reasons: Optional list of matching reasons.
            language: "zh" for Chinese, "en" for English.
            
        Returns:
            Generated letter content.
        """
        # Build context about the student
        student_info = self._format_student_info(profile)
        
        # Build context about the professor
        professor_info = self._format_professor_info(professor)

        # Build the prompt
        lang_instruction = "请用中文撰写邮件。" if language == "zh" else "Please write in English."
        
        user_prompt = f"""请为以下学生撰写一封给导师的学术联络邮件。

## 学生背景
{student_info}

## 目标导师信息
{professor_info}

## 匹配亮点
{chr(10).join(f'- {r}' for r in (match_reasons or [])) if match_reasons else '无特定匹配信息'}

{lang_instruction}

请撰写邮件："""

        # Call the LLM
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    def _format_student_info(self, profile: UserProfile) -> str:
        """Format student profile for the prompt."""
        parts = []

        if profile.name:
            parts.append(f"姓名：{profile.name}")

        # Education
        if profile.education:
            edu_lines = []
            for edu in profile.education:
                line = f"- {edu.get('degree', '未知')}: {edu.get('school', '未知')}"
                if edu.get('major'):
                    line += f" ({edu['major']})"
                edu_lines.append(line)
            parts.append("教育背景：\n" + "\n".join(edu_lines))

        # Research experience
        if profile.research_experience:
            exp_lines = []
            for exp in profile.research_experience:
                line = f"- {exp.get('title', '研究经历')}"
                if exp.get('organization'):
                    line += f" @ {exp['organization']}"
                if exp.get('description'):
                    line += f"\n  {exp['description'][:200]}"
                exp_lines.append(line)
            parts.append("科研经历：\n" + "\n".join(exp_lines))

        # Projects
        if profile.projects:
            proj_lines = [f"- {p.get('name', '项目')}" for p in profile.projects]
            parts.append("项目经历：\n" + "\n".join(proj_lines))

        # Skills
        if profile.skills:
            parts.append(f"技能专长：{', '.join(profile.skills)}")

        return "\n\n".join(parts) if parts else "无详细信息"

    def _format_professor_info(self, professor: Professor) -> str:
        """Format professor info for the prompt."""
        parts = []

        parts.append(f"姓名：{professor.name}")
        
        if professor.affiliation:
            parts.append(f"单位：{professor.affiliation}")

        if professor.research_interests:
            parts.append(f"研究方向：{', '.join(professor.research_interests)}")

        # Include some publications
        if professor.publications:
            pub_lines = []
            for pub in professor.publications[:5]:
                title = pub.get('title', '')
                year = pub.get('year', '')
                if title:
                    pub_lines.append(f"- {title} ({year})")
            if pub_lines:
                parts.append("代表论文：\n" + "\n".join(pub_lines))

        if professor.h_index:
            parts.append(f"H-Index：{professor.h_index}")

        return "\n".join(parts)
