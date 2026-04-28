"""LLM-based resume parser using DeepSeek API."""

import json
import re
import logging
from typing import Optional
from openai import OpenAI

from ..config import settings
from ..prompts import get_prompt
from .base import (
    BaseParser,
    ParsedResume,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
)


logger = logging.getLogger(__name__)


class LLMParserError(Exception):
    """Exception raised when LLM parsing fails."""

    pass


class LLMParser(BaseParser):
    """Parser that uses LLM (DeepSeek API) to extract resume information."""

    MAX_RETRIES = 2

    def __init__(self):
        """Initialize the LLM parser."""
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured in .env")

        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    @staticmethod
    def supported_extensions() -> list[str]:
        """LLM parser supports all text-based formats."""
        return [".md", ".markdown", ".tex", ".latex", ".txt"]

    def parse(self, content: str) -> ParsedResume:
        """Parse resume content using LLM.

        Args:
            content: Raw resume content string.

        Returns:
            ParsedResume with extracted data.

        Raises:
            LLMParserError: If parsing fails after all retries.
        """
        if not content.strip():
            raise LLMParserError("Empty content provided")

        # Get prompts
        system_prompt = get_prompt("resume_parser", "resume_extraction", "system")
        user_prompt = get_prompt("resume_parser", "resume_extraction", "user", content=content)

        # Try to call LLM with retries
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self._call_llm(system_prompt, user_prompt)
                parsed_data = self._parse_json_response(response)
                return self._convert_to_parsed_resume(parsed_data, content)
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parsing failed (attempt {attempt + 1}): {e}")
                if attempt < self.MAX_RETRIES:
                    # Try to fix JSON on retry
                    continue
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")
                if attempt < self.MAX_RETRIES:
                    continue
                break

        raise LLMParserError(
            f"Failed to parse resume after {self.MAX_RETRIES + 1} attempts: {last_error}"
        )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM API.

        Args:
            system_prompt: System message for the LLM.
            user_prompt: User message with the resume content.

        Returns:
            LLM response content.
        """
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistent structured output
            max_tokens=2000,
        )
        return response.choices[0].message.content

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed JSON dictionary.

        Raises:
            json.JSONDecodeError: If JSON parsing fails.
        """
        # Try direct parsing first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to find JSON object in the response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        # Give up
        raise json.JSONDecodeError("No valid JSON found in response", response, 0)

    def _convert_to_parsed_resume(self, data: dict, raw_content: str) -> ParsedResume:
        """Convert parsed JSON data to ParsedResume object.

        Args:
            data: Parsed JSON dictionary.
            raw_content: Original resume content.

        Returns:
            ParsedResume object.
        """
        # Parse education entries
        education = []
        for edu in data.get("education", []) or []:
            if isinstance(edu, dict):
                education.append(
                    EducationEntry(
                        degree=edu.get("degree", "未知"),
                        school=edu.get("school", "未知"),
                        major=edu.get("major"),
                        period=edu.get("period"),
                    )
                )

        # Parse research experience entries
        research_experience = []
        for exp in data.get("research_experience", []) or []:
            if isinstance(exp, dict):
                research_experience.append(
                    ExperienceEntry(
                        title=exp.get("title", "研究经历"),
                        organization=exp.get("organization"),
                        description=exp.get("description", ""),
                        period=exp.get("period"),
                    )
                )

        # Parse project entries
        projects = []
        for proj in data.get("projects", []) or []:
            if isinstance(proj, dict):
                projects.append(
                    ProjectEntry(
                        name=proj.get("name", "项目"),
                        description=proj.get("description", ""),
                    )
                )

        # Parse skills
        skills = []
        raw_skills = data.get("skills", []) or []
        if isinstance(raw_skills, list):
            skills = [str(s) for s in raw_skills if s]

        return ParsedResume(
            name=data.get("name"),
            education=education,
            research_experience=research_experience,
            projects=projects,
            skills=skills,
            raw_content=raw_content,
        )
