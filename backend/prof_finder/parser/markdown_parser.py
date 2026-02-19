"""Markdown resume parser."""

import re
from typing import Optional
from .base import (
    BaseParser,
    ParsedResume,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
)


class MarkdownParser(BaseParser):
    """Parser for Markdown format resumes."""

    # Section header patterns (English and Chinese)
    EDUCATION_PATTERNS = [
        r"education",
        r"教育背景",
        r"教育经历",
        r"学历",
        r"academic background",
    ]
    RESEARCH_PATTERNS = [
        r"research",
        r"科研经历",
        r"研究经历",
        r"科研背景",
        r"research experience",
        r"work experience",
        r"工作经历",
    ]
    PROJECT_PATTERNS = [
        r"project",
        r"项目",
        r"项目经历",
        r"projects",
    ]
    SKILL_PATTERNS = [
        r"skill",
        r"技能",
        r"专长",
        r"技术栈",
        r"technical skills",
        r"expertise",
    ]

    # Degree keywords
    DEGREE_KEYWORDS = {
        "本科": "本科",
        "学士": "本科",
        "bachelor": "本科",
        "b.s.": "本科",
        "b.a.": "本科",
        "undergraduate": "本科",
        "硕士": "硕士",
        "master": "硕士",
        "m.s.": "硕士",
        "m.a.": "硕士",
        "mphil": "硕士",
        "博士": "博士",
        "phd": "博士",
        "ph.d.": "博士",
        "doctor": "博士",
    }

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".md", ".markdown"]

    def parse(self, content: str) -> ParsedResume:
        """Parse Markdown resume content."""
        result = ParsedResume(raw_content=content)

        # Try to extract name from first heading
        result.name = self._extract_name(content)

        # Split content into sections
        sections = self._split_sections(content)

        for section_title, section_content in sections.items():
            title_lower = section_title.lower()

            if self._matches_patterns(title_lower, self.EDUCATION_PATTERNS):
                result.education = self._parse_education(section_content)
            elif self._matches_patterns(title_lower, self.RESEARCH_PATTERNS):
                result.research_experience = self._parse_experience(section_content)
            elif self._matches_patterns(title_lower, self.PROJECT_PATTERNS):
                result.projects = self._parse_projects(section_content)
            elif self._matches_patterns(title_lower, self.SKILL_PATTERNS):
                result.skills = self._parse_skills(section_content)

        return result

    def _extract_name(self, content: str) -> Optional[str]:
        """Extract name from first H1 heading or first line."""
        # Try H1 heading
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            name = h1_match.group(1).strip()
            # Skip if it looks like a section title
            if not self._is_section_title(name):
                return name

        # Try first non-empty line
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Skip if it looks like a section title
                if not self._is_section_title(line) and len(line) < 50:
                    return line
                break
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
        """Split content into sections by headers."""
        sections = {}
        current_section = ""
        current_content = []

        for line in content.split("\n"):
            # Check for header (## or ###)
            header_match = re.match(r"^#{1,3}\s+(.+)$", line)
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = header_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _matches_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the patterns."""
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _parse_education(self, content: str) -> list[EducationEntry]:
        """Parse education section."""
        entries = []
        lines = [l.strip() for l in content.split("\n") if l.strip()]

        for line in lines:
            # Remove list markers
            line = re.sub(r"^[-*•]\s*", "", line)
            if not line:
                continue

            entry = self._parse_education_line(line)
            if entry:
                entries.append(entry)

        return entries

    def _parse_education_line(self, line: str) -> Optional[EducationEntry]:
        """Parse a single education line."""
        # Try to extract degree
        degree = None
        for keyword, degree_name in self.DEGREE_KEYWORDS.items():
            if keyword in line.lower():
                degree = degree_name
                break

        if not degree:
            degree = "未知"

        # Try to extract school (often the longest capitalized word sequence or Chinese name)
        # Simple heuristic: look for university/大学 patterns
        school_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:University|College|Institute))", line)
        if not school_match:
            school_match = re.search(r"([\u4e00-\u9fff]+(?:大学|学院|研究院))", line)
        
        school = school_match.group(1) if school_match else line[:50]

        # Try to extract major
        major_match = re.search(r"(?:专业|major|in)\s*[:：]?\s*(.+?)(?:\s*[,，]|\s*\d|$)", line, re.IGNORECASE)
        major = major_match.group(1).strip() if major_match else None

        # Try to extract period
        period_match = re.search(r"(\d{4}\s*[-–—]\s*\d{4}|\d{4}\s*[-–—]\s*(?:present|至今|现在))", line, re.IGNORECASE)
        period = period_match.group(1) if period_match else None

        return EducationEntry(degree=degree, school=school, major=major, period=period)

    def _parse_experience(self, content: str) -> list[ExperienceEntry]:
        """Parse research/work experience section."""
        entries = []
        current_entry = None
        
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new entry (starts with list marker or bold)
            is_new_entry = bool(re.match(r"^[-*•]|\*\*", line))
            
            if is_new_entry:
                if current_entry:
                    entries.append(current_entry)
                
                # Clean the line
                title = re.sub(r"^[-*•]\s*", "", line)
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)  # Remove bold markers
                
                # Try to extract organization
                org_match = re.search(r"[@＠]\s*(.+?)(?:\s*[,，]|$)", title)
                org = org_match.group(1).strip() if org_match else None
                if org:
                    title = title.replace(org_match.group(0), "").strip()
                
                # Try to extract period
                period_match = re.search(r"(\d{4}\s*[-–—]\s*\d{4}|\d{4}\s*[-–—]\s*(?:present|至今|现在))", title, re.IGNORECASE)
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
                # Add to description
                desc_line = re.sub(r"^\s*[-*•]\s*", "", line)
                if current_entry.description:
                    current_entry.description += " " + desc_line
                else:
                    current_entry.description = desc_line

        if current_entry:
            entries.append(current_entry)

        return entries

    def _parse_projects(self, content: str) -> list[ProjectEntry]:
        """Parse projects section."""
        entries = []
        current_entry = None

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new project
            is_new_entry = bool(re.match(r"^[-*•]|\*\*", line))

            if is_new_entry:
                if current_entry:
                    entries.append(current_entry)

                name = re.sub(r"^[-*•]\s*", "", line)
                name = re.sub(r"\*\*(.+?)\*\*", r"\1", name)
                
                current_entry = ProjectEntry(name=name.strip(), description="")
            elif current_entry:
                desc_line = re.sub(r"^\s*[-*•]\s*", "", line)
                if current_entry.description:
                    current_entry.description += " " + desc_line
                else:
                    current_entry.description = desc_line

        if current_entry:
            entries.append(current_entry)

        return entries

    def _parse_skills(self, content: str) -> list[str]:
        """Parse skills section."""
        skills = []

        # Try to extract from list items
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Remove list markers
            line = re.sub(r"^[-*•]\s*", "", line)
            
            # Split by common delimiters
            parts = re.split(r"[,，;；、/]", line)
            for part in parts:
                skill = part.strip()
                if skill and len(skill) < 50:  # Reasonable skill name length
                    skills.append(skill)

        return skills
