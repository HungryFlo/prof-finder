"""Base parser interface and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EducationEntry:
    """Education background entry."""

    degree: str  # e.g., "本科", "硕士", "Bachelor", "Master"
    school: str
    major: Optional[str] = None
    period: Optional[str] = None  # e.g., "2018-2022"

    def to_dict(self) -> dict:
        return {
            "degree": self.degree,
            "school": self.school,
            "major": self.major,
            "period": self.period,
        }


@dataclass
class ExperienceEntry:
    """Research or work experience entry."""

    title: str  # Position or project title
    organization: Optional[str] = None
    description: str = ""
    period: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "organization": self.organization,
            "description": self.description,
            "period": self.period,
        }


@dataclass
class ProjectEntry:
    """Project entry."""

    name: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
        }


@dataclass
class ParsedResume:
    """Parsed resume data structure."""

    name: Optional[str] = None
    education: list[EducationEntry] = field(default_factory=list)
    research_experience: list[ExperienceEntry] = field(default_factory=list)
    projects: list[ProjectEntry] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    raw_content: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "education": [e.to_dict() for e in self.education],
            "research_experience": [e.to_dict() for e in self.research_experience],
            "projects": [p.to_dict() for p in self.projects],
            "skills": self.skills,
        }

    def is_empty(self) -> bool:
        """Check if parsing extracted any meaningful data."""
        return not any([
            self.name,
            self.education,
            self.research_experience,
            self.projects,
            self.skills,
        ])


class BaseParser(ABC):
    """Abstract base class for resume parsers."""

    @abstractmethod
    def parse(self, content: str) -> ParsedResume:
        """Parse resume content and extract structured data.

        Args:
            content: Raw resume content string.

        Returns:
            ParsedResume with extracted data.
        """
        pass

    @staticmethod
    @abstractmethod
    def supported_extensions() -> list[str]:
        """Return list of supported file extensions.

        Returns:
            List of extensions like [".md", ".markdown"]
        """
        pass

    def parse_file(self, file_path: str) -> ParsedResume:
        """Parse resume from file.

        Args:
            file_path: Path to resume file.

        Returns:
            ParsedResume with extracted data.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse(content)
