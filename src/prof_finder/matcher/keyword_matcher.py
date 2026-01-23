"""Keyword-based matching algorithm."""

import re
from dataclasses import dataclass
from typing import Optional

from ..models import UserProfile, Professor


@dataclass
class MatchResult:
    """Result of matching a profile with a professor."""
    
    professor_id: int
    professor_name: str
    score: float  # 0-100
    reasons: list[str]
    
    def to_dict(self) -> dict:
        return {
            "professor_id": self.professor_id,
            "professor_name": self.professor_name,
            "score": self.score,
            "reasons": self.reasons,
        }


class KeywordMatcher:
    """Simple keyword-based matching algorithm."""

    # Weight configuration
    WEIGHTS = {
        "research_interest": 40,  # Research direction match
        "skill": 30,              # Skill match
        "publication": 20,        # Publication topic match
        "education": 10,          # Education background
    }

    def __init__(self):
        """Initialize the matcher."""
        pass

    def match(self, profile: UserProfile, professor: Professor) -> MatchResult:
        """Calculate match score between a profile and professor.
        
        Args:
            profile: User profile to match.
            professor: Professor to match against.
            
        Returns:
            MatchResult with score and reasons.
        """
        score = 0.0
        reasons = []

        # Extract keywords from profile
        profile_keywords = self._extract_profile_keywords(profile)
        
        # Match research interests
        interest_score, interest_reasons = self._match_interests(
            profile_keywords, professor.research_interests or []
        )
        score += interest_score * self.WEIGHTS["research_interest"] / 100
        reasons.extend(interest_reasons)

        # Match skills with publications
        skill_score, skill_reasons = self._match_skills_with_publications(
            profile.skills or [], professor.publications or []
        )
        score += skill_score * self.WEIGHTS["skill"] / 100
        reasons.extend(skill_reasons)

        # Match research experience with publications
        pub_score, pub_reasons = self._match_experience_with_publications(
            profile.research_experience or [], professor.publications or []
        )
        score += pub_score * self.WEIGHTS["publication"] / 100
        reasons.extend(pub_reasons)

        # Education bonus (having relevant degree)
        edu_score, edu_reasons = self._match_education(
            profile.education or [], professor.affiliation or ""
        )
        score += edu_score * self.WEIGHTS["education"] / 100
        reasons.extend(edu_reasons)

        return MatchResult(
            professor_id=professor.id,
            professor_name=professor.name,
            score=min(score, 100.0),  # Cap at 100
            reasons=reasons,
        )

    def _extract_profile_keywords(self, profile: UserProfile) -> set[str]:
        """Extract keywords from user profile."""
        keywords = set()

        # From skills
        for skill in (profile.skills or []):
            keywords.add(skill.lower())

        # From research experience
        for exp in (profile.research_experience or []):
            desc = exp.get("description", "") + " " + exp.get("title", "")
            keywords.update(self._extract_keywords(desc))

        # From projects
        for proj in (profile.projects or []):
            desc = proj.get("description", "") + " " + proj.get("name", "")
            keywords.update(self._extract_keywords(desc))

        return keywords

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract meaningful keywords from text."""
        # Common technical terms to look for
        tech_terms = [
            "machine learning", "deep learning", "nlp", "natural language",
            "computer vision", "reinforcement learning", "neural network",
            "transformer", "bert", "gpt", "llm", "language model",
            "classification", "detection", "segmentation", "recognition",
            "generation", "translation", "summarization", "question answering",
            "robotics", "autonomous", "optimization", "distributed",
            "database", "system", "security", "network", "cloud",
            "python", "tensorflow", "pytorch", "java", "c++",
            "data mining", "knowledge graph", "recommendation",
        ]

        text_lower = text.lower()
        found = set()

        for term in tech_terms:
            if term in text_lower:
                found.add(term)

        # Also extract capitalized words (might be tech terms)
        words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        for word in words:
            if len(word) > 3:
                found.add(word.lower())

        return found

    def _match_interests(
        self, profile_keywords: set[str], professor_interests: list[str]
    ) -> tuple[float, list[str]]:
        """Match profile keywords with professor research interests."""
        if not professor_interests:
            return 0.0, []

        matches = []
        prof_interests_lower = [i.lower() for i in professor_interests]

        for keyword in profile_keywords:
            for interest in prof_interests_lower:
                if keyword in interest or interest in keyword:
                    matches.append(interest)
                    break

        if not matches:
            return 0.0, []

        # Score based on proportion of matching interests
        score = min(len(matches) / len(professor_interests) * 100, 100)
        unique_matches = list(set(matches))[:3]
        reasons = [f"研究方向匹配: {', '.join(unique_matches)}"]
        
        return score, reasons

    def _match_skills_with_publications(
        self, skills: list[str], publications: list[dict]
    ) -> tuple[float, list[str]]:
        """Match skills with publication topics."""
        if not skills or not publications:
            return 0.0, []

        # Extract keywords from publication titles
        pub_text = " ".join(pub.get("title", "") for pub in publications[:10])
        pub_keywords = self._extract_keywords(pub_text)

        matches = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in pub_keywords:
                matches.append(skill)
            elif any(skill_lower in kw for kw in pub_keywords):
                matches.append(skill)

        if not matches:
            return 0.0, []

        score = min(len(matches) / len(skills) * 100, 100)
        reasons = [f"技能与论文匹配: {', '.join(matches[:3])}"]
        
        return score, reasons

    def _match_experience_with_publications(
        self, experiences: list[dict], publications: list[dict]
    ) -> tuple[float, list[str]]:
        """Match research experience with professor's publications."""
        if not experiences or not publications:
            return 0.0, []

        # Extract keywords from experiences
        exp_text = " ".join(
            exp.get("description", "") + " " + exp.get("title", "")
            for exp in experiences
        )
        exp_keywords = self._extract_keywords(exp_text)

        # Extract keywords from publications
        pub_text = " ".join(pub.get("title", "") for pub in publications[:10])
        pub_keywords = self._extract_keywords(pub_text)

        # Find common keywords
        common = exp_keywords & pub_keywords

        if not common:
            return 0.0, []

        score = min(len(common) * 20, 100)  # Each common keyword adds 20 points
        reasons = [f"研究经历与论文主题相关: {', '.join(list(common)[:3])}"]
        
        return score, reasons

    def _match_education(
        self, education: list[dict], affiliation: str
    ) -> tuple[float, list[str]]:
        """Match education background."""
        if not education:
            return 0.0, []

        # Check for PhD or Master's degree
        has_advanced_degree = False
        for edu in education:
            degree = edu.get("degree", "").lower()
            if "博士" in degree or "phd" in degree:
                has_advanced_degree = True
                break
            if "硕士" in degree or "master" in degree:
                has_advanced_degree = True

        if has_advanced_degree:
            return 50.0, ["具有研究生学历"]

        return 20.0, []
