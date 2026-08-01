"""LaTeX resume parser."""

import re
from typing import Optional

from .base import (
    BaseParser,
    EducationEntry,
    ExperienceEntry,
    ParsedResume,
    ProjectEntry,
)


class LaTeXParser(BaseParser):
    """Parser for LaTeX format resumes."""

    # Section header patterns
    EDUCATION_PATTERNS = [
        r"education",
        r"教育背景",
        r"教育经历",
        r"学历",
    ]
    RESEARCH_PATTERNS = [
        r"research",
        r"experience",
        r"科研",
        r"研究经历",
        r"工作经历",
    ]
    PROJECT_PATTERNS = [
        r"project",
        r"项目",
    ]
    SKILL_PATTERNS = [
        r"skill",
        r"技能",
        r"专长",
    ]

    # Degree keywords
    DEGREE_KEYWORDS = {
        "本科": "本科",
        "学士": "本科",
        "bachelor": "本科",
        "b.s.": "本科",
        "undergraduate": "本科",
        "硕士": "硕士",
        "master": "硕士",
        "m.s.": "硕士",
        "mphil": "硕士",
        "博士": "博士",
        "phd": "博士",
        "doctor": "博士",
    }

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".tex", ".latex"]

    def parse(self, content: str) -> ParsedResume:
        """Parse LaTeX resume content."""
        result = ParsedResume(raw_content=content)

        # Convert LaTeX to plain text first
        plain_text = self._latex_to_text(content)

        # Extract name
        result.name = self._extract_name(content, plain_text)

        # Split into sections
        sections = self._split_sections(content)

        for section_title, section_content in sections.items():
            title_lower = section_title.lower()
            plain_content = self._latex_to_text(section_content)

            if self._matches_patterns(title_lower, self.EDUCATION_PATTERNS):
                result.education = self._parse_education(plain_content)
            elif self._matches_patterns(title_lower, self.RESEARCH_PATTERNS):
                result.research_experience = self._parse_experience(plain_content)
            elif self._matches_patterns(title_lower, self.PROJECT_PATTERNS):
                result.projects = self._parse_projects(plain_content)
            elif self._matches_patterns(title_lower, self.SKILL_PATTERNS):
                result.skills = self._parse_skills(plain_content)

        return result

    def _latex_to_text(self, content: str) -> str:
        """Convert LaTeX content to plain text."""
        text = content

        # Remove comments
        text = re.sub(r"(?<!\\)%.*$", "", text, flags=re.MULTILINE)

        # Handle common commands
        # \textbf{...}, \textit{...}, \emph{...}
        text = re.sub(r"\\text(?:bf|it|tt|sc|sf|rm)\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)

        # \href{url}{text}
        text = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", text)

        # \url{...}
        text = re.sub(r"\\url\{([^}]*)\}", r"\1", text)

        # Remove \item markers but keep content
        text = re.sub(r"\\item\s*", "\n• ", text)

        # Remove section/subsection commands but keep title
        text = re.sub(r"\\(?:sub)*section\*?\{([^}]*)\}", r"\n\1\n", text)

        # Remove common environments
        text = re.sub(r"\\begin\{(?:itemize|enumerate|description|center)\}", "", text)
        text = re.sub(r"\\end\{(?:itemize|enumerate|description|center)\}", "", text)

        # Remove document structure commands
        text = re.sub(r"\\(?:documentclass|usepackage|begin|end)\{[^}]*\}(?:\[[^\]]*\])?", "", text)
        text = re.sub(r"\\(?:document|maketitle|tableofcontents|newpage|clearpage)", "", text)

        # Remove spacing commands
        text = re.sub(r"\\(?:vspace|hspace|vfill|hfill|quad|qquad|,|;|!)\*?\{?[^}]*\}?", " ", text)
        text = re.sub(r"\\\\", "\n", text)  # Line breaks

        # Remove remaining simple commands
        text = re.sub(r"\\[a-zA-Z]+\*?(?:\{[^}]*\})?", "", text)

        # Clean up braces
        text = re.sub(r"[{}]", "", text)

        # Clean up whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _extract_name(self, latex_content: str, plain_text: str) -> Optional[str]:
        """Extract name from LaTeX content."""
        # Try to find \name{...} command
        name_match = re.search(r"\\name\{([^}]+)\}", latex_content)
        if name_match:
            return name_match.group(1).strip()

        # Try \author{...}
        author_match = re.search(r"\\author\{([^}]+)\}", latex_content)
        if author_match:
            return author_match.group(1).strip()

        # Try first line of plain text
        lines = plain_text.strip().split("\n")
        for line in lines[:3]:
            line = line.strip()
            if line and len(line) < 50 and not self._is_section_title(line):
                return line

        return None

    def _is_section_title(self, text: str) -> bool:
        """Check if text looks like a section title."""
        text_lower = text.lower()
        all_patterns = (
            self.EDUCATION_PATTERNS
            + self.RESEARCH_PATTERNS
            + self.PROJECT_PATTERNS
            + self.SKILL_PATTERNS
        )
        return any(re.search(p, text_lower) for p in all_patterns)

    def _split_sections(self, content: str) -> dict[str, str]:
        """Split LaTeX content into sections."""
        sections = {}

        # Find all section/subsection commands
        pattern = r"\\(?:sub)*section\*?\{([^}]+)\}"
        matches = list(re.finditer(pattern, content))

        for i, match in enumerate(matches):
            section_title = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections[section_title] = content[start:end]

        return sections

    def _matches_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any pattern."""
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _parse_education(self, content: str) -> list[EducationEntry]:
        """Parse education section from plain text."""
        entries = []
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        for line in lines:
            # Skip bullet markers
            line = re.sub(r"^[•\-*]\s*", "", line)
            if not line or len(line) < 5:
                continue

            entry = self._parse_education_line(line)
            if entry:
                entries.append(entry)

        return entries

    def _parse_education_line(self, line: str) -> Optional[EducationEntry]:
        """Parse education entry from a line."""
        # Detect degree
        degree = "未知"
        for keyword, degree_name in self.DEGREE_KEYWORDS.items():
            if keyword in line.lower():
                degree = degree_name
                break

        # Extract school
        school_match = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:University|College|Institute))",
            line,
        )
        if not school_match:
            school_match = re.search(r"([\u4e00-\u9fff]+(?:大学|学院|研究院))", line)

        school = school_match.group(1) if school_match else line[:50]

        # Extract major
        major_match = re.search(
            r"(?:专业|major|in)\s*[:：]?\s*(.+?)(?:\s*[,，]|\s*\d|$)",
            line,
            re.IGNORECASE,
        )
        major = major_match.group(1).strip() if major_match else None

        # Extract period
        period_match = re.search(
            r"(\d{4}\s*[-–—]\s*\d{4}|\d{4}\s*[-–—]\s*(?:present|至今))",
            line,
            re.IGNORECASE,
        )
        period = period_match.group(1) if period_match else None

        return EducationEntry(degree=degree, school=school, major=major, period=period)

    def _parse_experience(self, content: str) -> list[ExperienceEntry]:
        """Parse experience section."""
        entries = []
        current_entry = None

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for new entry
            is_new = line.startswith("•") or (len(line) > 10 and not line.startswith(" "))

            if is_new:
                if current_entry:
                    entries.append(current_entry)

                title = re.sub(r"^[•\-*]\s*", "", line)

                # Extract organization
                org_match = re.search(r"[@＠]\s*(.+?)(?:\s*[,，]|$)", title)
                org = org_match.group(1).strip() if org_match else None
                if org:
                    title = title.replace(org_match.group(0), "").strip()

                # Extract period
                period_match = re.search(
                    r"(\d{4}\s*[-–—]\s*\d{4}|\d{4}\s*[-–—]\s*(?:present|至今))",
                    title,
                    re.IGNORECASE,
                )
                period = period_match.group(1) if period_match else None
                if period:
                    title = title.replace(period, "").strip()

                current_entry = ExperienceEntry(
                    title=title.strip(" ,，"),
                    organization=org,
                    period=period,
                    description="",
                )
            elif current_entry:
                desc = re.sub(r"^[•\-*]\s*", "", line)
                if current_entry.description:
                    current_entry.description += " " + desc
                else:
                    current_entry.description = desc

        if current_entry:
            entries.append(current_entry)

        return entries

    def _parse_projects(self, content: str) -> list[ProjectEntry]:
        """Parse projects section."""
        entries = []
        current_entry = None

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            is_new = line.startswith("•") or (len(line) > 5 and not line.startswith(" "))

            if is_new:
                if current_entry:
                    entries.append(current_entry)

                name = re.sub(r"^[•\-*]\s*", "", line)
                current_entry = ProjectEntry(name=name.strip(), description="")
            elif current_entry:
                desc = re.sub(r"^[•\-*]\s*", "", line)
                if current_entry.description:
                    current_entry.description += " " + desc
                else:
                    current_entry.description = desc

        if current_entry:
            entries.append(current_entry)

        return entries

    def _parse_skills(self, content: str) -> list[str]:
        """Parse skills section."""
        skills = []

        for line in content.split("\n"):
            line = re.sub(r"^[•\-*]\s*", "", line.strip())
            if not line:
                continue

            # Split by delimiters
            parts = re.split(r"[,，;；、/]", line)
            for part in parts:
                skill = part.strip()
                if skill and len(skill) < 50:
                    skills.append(skill)

        return skills
