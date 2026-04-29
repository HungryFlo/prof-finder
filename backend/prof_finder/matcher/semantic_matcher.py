"""Semantic matching using allenai-specter sentence-transformer embeddings."""

from __future__ import annotations

from typing import Optional
from pathlib import Path

import numpy as np

# Singleton — loaded once, reused across all match tasks in the process lifetime.
_model = None
_LOCAL_MODEL_PATH = Path(__file__).resolve().parents[2] / "allenai-specter"


def _get_model():
    """Lazily load the allenai-specter model, preferring local disk cache."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        if _LOCAL_MODEL_PATH.exists():
            # Force local load to avoid runtime download/network flakiness.
            _model = SentenceTransformer(str(_LOCAL_MODEL_PATH), local_files_only=True)
        else:
            _model = SentenceTransformer("allenai-specter")
    return _model


# ---------------------------------------------------------------------------
# Text builders
# ---------------------------------------------------------------------------

def build_professor_text(professor: dict) -> str:
    """Serialise professor data to a string for encoding.

    Uses allenai-specter's training convention: title [SEP] body.
    Title = research interests (or generated profile); body = publication titles + affiliation.

    When a generated research profile is available, it becomes the primary text with
    research interests, publication titles, paper summaries, and affiliation as supporting signals.
    """
    research_profile = (professor.get("research_profile") or "").strip()
    research_profile_analysis = professor.get("research_profile_analysis") or {}

    # Build title from generated profile when available, otherwise from research interests.
    if research_profile:
        analysis_parts: list[str] = []
        if isinstance(research_profile_analysis, dict):
            positioning = research_profile_analysis.get("research_positioning")
            if positioning:
                analysis_parts.append(str(positioning))
            themes = research_profile_analysis.get("research_themes") or []
            if isinstance(themes, list):
                for item in themes:
                    if isinstance(item, dict):
                        theme = item.get("theme")
                        if theme:
                            analysis_parts.append(str(theme))
        title = ". ".join(p for p in
                          ([research_profile[:800]] + analysis_parts)
                          if p)
    else:
        interests = "; ".join(professor.get("research_interests") or [])
        title = interests

    pubs = professor.get("publications") or []
    pub_titles = ". ".join(
        p.get("title", "") for p in pubs[:15] if p.get("title")
    )
    affiliation = professor.get("affiliation") or ""
    paper_summaries = professor.get("paper_summaries") or []
    summary_text = ". ".join(
        f"{item.get('title', '')} {item.get('summary', '')}".strip()
        for item in paper_summaries[:20]
    )
    body_parts = [p for p in [pub_titles, summary_text, affiliation] if p]
    body = ". ".join(body_parts)
    return f"{title} [SEP] {body}"


def build_profile_text(profile: dict) -> str:
    """Serialise user profile data to a string for encoding."""
    academic_profile = (profile.get("academic_profile") or "").strip()
    analysis = profile.get("profile_analysis") or {}
    analysis_parts: list[str] = []
    if isinstance(analysis, dict):
        positioning = analysis.get("academic_positioning")
        if positioning:
            analysis_parts.append(str(positioning))
        for key in ("research_interests", "target_directions", "methods_and_skills"):
            values = analysis.get(key) or []
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, dict):
                        text = item.get("topic") or item.get("direction") or item.get("name")
                        if text:
                            analysis_parts.append(str(text))
                    elif item:
                        analysis_parts.append(str(item))

    skills = "; ".join(profile.get("skills") or [])

    experiences = profile.get("research_experience") or []
    exp_parts = [
        f"{e.get('title', '')} {e.get('description', '')}".strip()
        for e in experiences
    ]
    exp_text = ". ".join(p for p in exp_parts if p)

    projects = profile.get("projects") or []
    proj_parts = [
        f"{p.get('name', '')} {p.get('description', '')}".strip()
        for p in projects
    ]
    proj_text = ". ".join(p for p in proj_parts if p)

    generated_text = ". ".join(p for p in [academic_profile, *analysis_parts] if p)
    body_parts = [p for p in [generated_text, exp_text, proj_text] if p]
    body = ". ".join(body_parts)
    return f"{skills} [SEP] {body}"


# ---------------------------------------------------------------------------
# Batch encoding helpers (used by task_manager)
# ---------------------------------------------------------------------------

def encode_texts(texts: list[str]) -> np.ndarray:
    """Encode a list of texts into L2-normalised embedding vectors.

    Returns:
        ndarray of shape (N, 768), float32, L2-normalised.
    """
    model = _get_model()
    return model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)


def encode_text(text: str) -> list[float]:
    """Encode a single text, returning a plain Python list for JSON storage."""
    return encode_texts([text])[0].tolist()


# ---------------------------------------------------------------------------
# SemanticMatcher
# ---------------------------------------------------------------------------

class SemanticMatcher:
    """Match a user profile against a professor using cosine similarity."""

    def match(
        self,
        profile: dict,
        professor: dict,
        professor_embedding: Optional[list[float]] = None,
        profile_embedding: Optional[list[float]] = None,
    ) -> tuple[float, list[str]]:
        """Compute semantic match score.

        Args:
            profile: User profile dict (skills, research_experience, projects, …).
            professor: Professor dict (research_interests, publications, affiliation, …).
            professor_embedding: Pre-computed L2-normalised professor vector. If None,
                the professor text is encoded on the fly (slow — prefer caching).
            profile_embedding: Pre-computed L2-normalised profile vector. If None,
                the profile text is encoded on the fly. Pass this when matching one
                profile against many professors to avoid re-encoding each time.

        Returns:
            (score in [0, 100], human-readable reasons).
        """
        if profile_embedding is not None:
            profile_vec = np.array(profile_embedding, dtype=np.float32)
        else:
            profile_vec = np.array(encode_text(build_profile_text(profile)), dtype=np.float32)

        if professor_embedding is not None:
            prof_vec = np.array(professor_embedding, dtype=np.float32)
        else:
            prof_vec = np.array(encode_text(build_professor_text(professor)), dtype=np.float32)

        # Both vectors are L2-normalised, so dot product == cosine similarity.
        similarity = float(np.dot(profile_vec, prof_vec))
        score = (similarity + 1.0) / 2.0 * 100.0
        score = max(0.0, min(100.0, round(score, 2)))

        reasons = self._build_reasons(similarity, professor)
        return score, reasons

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reasons(similarity: float, professor: dict) -> list[str]:
        interests = professor.get("research_interests") or []
        if similarity > 0.6:
            level = "高度"
        elif similarity > 0.3:
            level = "较好"
        else:
            level = "一般"

        reasons: list[str] = []
        if interests:
            top = ", ".join(interests[:3])
            reasons.append(f"语义{level}匹配: {top}")
        reasons.append(f"语义相似度: {similarity:.2f}")
        return reasons
