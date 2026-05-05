"""Structured I/O types for AI workflow functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StudentProfileResult:
    """Output from student profile generation."""

    academic_profile: str
    profile_analysis: dict
    evidence_notes: list = field(default_factory=list)
    conflict_notes: list = field(default_factory=list)


@dataclass
class ProfessorProfileResult:
    """Output from professor profile generation."""

    research_profile: str
    research_profile_analysis: dict
    research_profile_sources: list = field(default_factory=list)
    research_profile_evidence: list = field(default_factory=list)
    research_profile_conflicts: list = field(default_factory=list)


@dataclass
class PaperSummaryResult:
    """Output from paper summarization."""

    summary: str
    keywords: list = field(default_factory=list)


@dataclass
class LetterStudentInfo:
    """Student information for letter generation (DB-free)."""

    name: str = ""
    name_locales: dict = field(default_factory=dict)
    education: list = field(default_factory=list)
    research_experience: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    academic_profile: str = ""
    profile_analysis: dict = field(default_factory=dict)


@dataclass
class LetterProfessorInfo:
    """Professor information for letter generation (DB-free)."""

    name: str = ""
    name_locales: dict = field(default_factory=dict)
    affiliation: str = ""
    research_interests: list = field(default_factory=list)
    publications: list = field(default_factory=list)
    research_profile: str = ""
    research_profile_analysis: dict = field(default_factory=dict)
    h_index: Optional[int] = None
