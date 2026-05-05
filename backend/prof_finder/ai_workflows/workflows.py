"""Pure AI workflow functions — DB-free, HTTP-free, independently testable.

Each function takes plain data and returns plain data. They use the existing
LLM generator classes internally but present a clean, framework-agnostic interface.
"""

from __future__ import annotations

from typing import Optional

from ..llm.letter_generator import LetterGenerator
from ..llm.paper_summarizer import PaperSummarizer
from ..llm.professor_profile_generator import ProfessorProfileGenerator
from ..llm.student_profile_generator import StudentProfileGenerator
from .provider import LLMProvider
from .schemas import (
    LetterProfessorInfo,
    LetterStudentInfo,
    PaperSummaryResult,
    ProfessorProfileResult,
    StudentProfileResult,
)


def generate_student_profile(
    materials: list[dict],
    manual_inputs: dict,
    previous_academic_profile: str = "",
    previous_profile_analysis: dict | None = None,
    language: str = "en",
    provider: LLMProvider | None = None,
) -> StudentProfileResult:
    """Generate an academic profile from student materials.

    Args:
        materials: List of material dicts with 'filename', 'source_type', 'content'.
        manual_inputs: Dict of manually entered fields.
        previous_academic_profile: Previous profile text for incremental update.
        previous_profile_analysis: Previous analysis dict for incremental update.
        language: Output language ('en' or 'zh').
        provider: Optional LLM provider; created from global config if omitted.

    Returns:
        StudentProfileResult with academic_profile, profile_analysis, etc.
    """
    generator = StudentProfileGenerator(provider=provider)
    result = generator.generate(
        materials=materials,
        manual_inputs=manual_inputs,
        previous_academic_profile=previous_academic_profile,
        previous_profile_analysis=previous_profile_analysis,
        language=language,
    )
    return StudentProfileResult(
        academic_profile=result["academic_profile"],
        profile_analysis=result["profile_analysis"],
        evidence_notes=result["evidence_notes"],
        conflict_notes=result["conflict_notes"],
    )


def generate_professor_profile(
    professor_data: dict,
    language: str = "en",
    provider: LLMProvider | None = None,
) -> ProfessorProfileResult:
    """Generate a research profile from professor data.

    Args:
        professor_data: Dict with keys like name, affiliation, research_interests,
            publications, paper_summaries, manual_notes, homepage, google_scholar_url.
        language: Output language ('en' or 'zh').
        provider: Optional LLM provider.

    Returns:
        ProfessorProfileResult with research_profile, analysis, sources, etc.
    """
    generator = ProfessorProfileGenerator(provider=provider)
    result = generator.generate(professor_data, language=language)
    return ProfessorProfileResult(
        research_profile=result["research_profile"],
        research_profile_analysis=result["research_profile_analysis"],
        research_profile_sources=result["research_profile_sources"],
        research_profile_evidence=result["research_profile_evidence"],
        research_profile_conflicts=result["research_profile_conflicts"],
    )


def generate_letter(
    student_info: LetterStudentInfo | dict,
    professor_info: LetterProfessorInfo | dict,
    match_reasons: list[str] | None = None,
    language: str = "en",
    provider: LLMProvider | None = None,
) -> str:
    """Generate an academic contact email.

    Args:
        student_info: LetterStudentInfo dataclass or compatible dict.
        professor_info: LetterProfessorInfo dataclass or compatible dict.
        match_reasons: Optional list of match highlight strings.
        language: 'zh' or 'en'.
        provider: Optional LLM provider.

    Returns:
        Generated email body string.
    """
    generator = LetterGenerator(provider=provider)

    # Convert dataclasses to dicts for the generator's flexible interface
    def _to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            from dataclasses import asdict
            return asdict(obj)
        return obj

    return generator.generate(
        profile=_to_dict(student_info),
        professor=_to_dict(professor_info),
        match_reasons=match_reasons,
        language=language,
    )


def summarize_paper(
    source_type: str,
    title: str,
    content: str,
    language: str = "en",
    provider: LLMProvider | None = None,
) -> PaperSummaryResult:
    """Summarize a paper using LLM with heuristic fallback.

    Args:
        source_type: Type of source (e.g., 'arxiv', 'pdf', 'scholar').
        title: Paper title.
        content: Paper text content.
        language: Output language.
        provider: Optional LLM provider.

    Returns:
        PaperSummaryResult with summary and keywords.
    """
    summarizer = PaperSummarizer(provider=provider)
    result = summarizer.summarize_with_fallback(
        source_type=source_type,
        title=title,
        content=content,
        language=language,
    )
    return PaperSummaryResult(
        summary=result["summary"],
        keywords=result["keywords"],
    )


def conduct_profile_interview(
    profile_analysis: dict,
    academic_profile: str,
    history: list[dict],
    message: str,
    locale: str = "zh",
    provider: LLMProvider | None = None,
) -> str:
    """Generate the next AI interviewer question based on profile gaps.

    Args:
        profile_analysis: Structured profile analysis JSON dict.
        academic_profile: Current readable Markdown profile.
        history: Chat history as [{role: "user"|"assistant", content: str}].
        message: Latest message from the student.
        locale: 'zh' or 'en'.
        provider: Optional LLM provider.

    Returns:
        AI interviewer reply string.
    """
    generator = StudentProfileGenerator(provider=provider)
    return generator.interview(
        profile_analysis=profile_analysis,
        academic_profile=academic_profile,
        history=history,
        message=message,
        locale=locale,
    )


def refine_profile_from_chat(
    materials: list[dict],
    manual_inputs: dict,
    chat_history: list[dict],
    academic_profile: str = "",
    profile_analysis: dict | None = None,
    language: str = "en",
    provider: LLMProvider | None = None,
) -> StudentProfileResult:
    """Regenerate a profile incorporating insights from chat Q&A.

    Args:
        materials: Original profile materials.
        manual_inputs: Original manual inputs dict.
        chat_history: Full chat history [{role, content}].
        academic_profile: Current readable profile (for incremental update).
        profile_analysis: Current analysis dict (for incremental update).
        language: Output language.
        provider: Optional LLM provider.

    Returns:
        StudentProfileResult with regenerated profile.
    """
    generator = StudentProfileGenerator(provider=provider)
    result = generator.refine_from_chat(
        materials=materials,
        manual_inputs=manual_inputs,
        chat_history=chat_history,
        academic_profile=academic_profile,
        profile_analysis=profile_analysis,
        language=language,
    )
    return StudentProfileResult(
        academic_profile=result["academic_profile"],
        profile_analysis=result["profile_analysis"],
        evidence_notes=result["evidence_notes"],
        conflict_notes=result["conflict_notes"],
    )
