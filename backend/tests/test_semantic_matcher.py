"""Unit tests for SemanticMatcher and its text-building helpers.

These tests use a lightweight mock to avoid loading the full allenai-specter
model (400 MB) during CI.  The mock returns deterministic L2-normalised vectors
that encode semantic similarity via simple dot-product arithmetic.
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from prof_finder.matcher.semantic_matcher import (
    SemanticMatcher,
    build_professor_text,
    build_profile_text,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _unit_vec(*components: float) -> np.ndarray:
    """Return an L2-normalised float32 vector."""
    v = np.array(components, dtype=np.float32)
    return v / np.linalg.norm(v)


# Two unit vectors whose cosine similarity can be controlled precisely.
_SIMILAR_A = _unit_vec(1.0, 0.0, 0.0)   # cos(A, B) = 1.0 → score = 100
_SIMILAR_B = _unit_vec(1.0, 0.0, 0.0)

_UNRELATED_A = _unit_vec(1.0, 0.0, 0.0)
_UNRELATED_B = _unit_vec(0.0, 1.0, 0.0)  # cos(A, B) = 0.0 → score = 50


# ---------------------------------------------------------------------------
# build_professor_text
# ---------------------------------------------------------------------------

class TestBuildProfessorText:
    def test_normal_input(self):
        prof = {
            "research_interests": ["NLP", "Machine Learning"],
            "publications": [{"title": "Attention Is All You Need"}, {"title": "BERT"}],
            "affiliation": "MIT",
        }
        text = build_professor_text(prof)
        assert "NLP" in text
        assert "Machine Learning" in text
        assert "Attention Is All You Need" in text
        assert "MIT" in text
        assert "[SEP]" in text

    def test_empty_fields(self):
        text = build_professor_text({})
        assert isinstance(text, str)
        assert "[SEP]" in text

    def test_none_fields(self):
        prof = {"research_interests": None, "publications": None, "affiliation": None}
        text = build_professor_text(prof)
        assert isinstance(text, str)

    def test_publications_capped_at_15(self):
        pubs = [{"title": f"Paper {i}"} for i in range(30)]
        text = build_professor_text({"publications": pubs})
        assert "Paper 14" in text
        assert "Paper 15" not in text

    def test_include_paper_summaries_in_professor_text(self):
        prof = {
            "research_interests": ["NLP"],
            "paper_summaries": [
                {"title": "Paper X", "summary": "This work studies language model alignment."}
            ],
        }
        text = build_professor_text(prof)
        assert "Paper X" in text
        assert "language model alignment" in text


# ---------------------------------------------------------------------------
# build_profile_text
# ---------------------------------------------------------------------------

class TestBuildProfileText:
    def test_normal_input(self):
        profile = {
            "skills": ["Python", "PyTorch"],
            "research_experience": [
                {"title": "NLP Intern", "description": "Built a text classifier"}
            ],
            "projects": [{"name": "Chatbot", "description": "Used BERT"}],
        }
        text = build_profile_text(profile)
        assert "Python" in text
        assert "NLP Intern" in text
        assert "Chatbot" in text
        assert "[SEP]" in text

    def test_empty_profile(self):
        text = build_profile_text({})
        assert isinstance(text, str)

    def test_none_fields(self):
        profile = {"skills": None, "research_experience": None, "projects": None}
        text = build_profile_text(profile)
        assert isinstance(text, str)

    def test_generated_academic_profile_has_priority(self):
        profile = {
            "skills": ["Python"],
            "academic_profile": "学生学术画像：关注 multimodal LLM safety.",
            "profile_analysis": {
                "academic_positioning": "AI safety applicant",
                "research_interests": [{"topic": "multimodal alignment"}],
            },
            "research_experience": [{"title": "Old Topic", "description": "robotics"}],
        }
        text = build_profile_text(profile)
        assert "multimodal LLM safety" in text
        assert "AI safety applicant" in text
        assert "multimodal alignment" in text
        assert "Old Topic" in text


# ---------------------------------------------------------------------------
# SemanticMatcher.match — score range and computation
# ---------------------------------------------------------------------------

class TestSemanticMatcherScore:
    """Tests use pre-computed embeddings to avoid model I/O."""

    def _make_matcher(self) -> SemanticMatcher:
        return SemanticMatcher()

    def test_score_in_range_identical_vectors(self):
        matcher = self._make_matcher()
        vec = _SIMILAR_A.tolist()
        score, _ = matcher.match(
            profile={},
            professor={},
            professor_embedding=vec,
            profile_embedding=vec,
        )
        assert 0.0 <= score <= 100.0
        assert math.isclose(score, 100.0, abs_tol=0.1)

    def test_score_in_range_orthogonal_vectors(self):
        matcher = self._make_matcher()
        score, _ = matcher.match(
            profile={},
            professor={},
            professor_embedding=_UNRELATED_B.tolist(),
            profile_embedding=_UNRELATED_A.tolist(),
        )
        assert 0.0 <= score <= 100.0
        assert math.isclose(score, 50.0, abs_tol=0.1)

    def test_similar_scores_higher_than_unrelated(self):
        matcher = self._make_matcher()

        similar_score, _ = matcher.match(
            profile={},
            professor={},
            professor_embedding=_SIMILAR_B.tolist(),
            profile_embedding=_SIMILAR_A.tolist(),
        )
        unrelated_score, _ = matcher.match(
            profile={},
            professor={},
            professor_embedding=_UNRELATED_B.tolist(),
            profile_embedding=_UNRELATED_A.tolist(),
        )
        assert similar_score > unrelated_score

    def test_reasons_contain_similarity_value(self):
        matcher = self._make_matcher()
        vec = _SIMILAR_A.tolist()
        _, reasons = matcher.match(
            profile={},
            professor={"research_interests": ["NLP"]},
            professor_embedding=vec,
            profile_embedding=vec,
        )
        assert any("语义相似度" in r for r in reasons)

    def test_reasons_high_similarity_label(self):
        matcher = self._make_matcher()
        vec = _SIMILAR_A.tolist()  # cosine = 1.0 > 0.6
        _, reasons = matcher.match(
            profile={},
            professor={"research_interests": ["deep learning"]},
            professor_embedding=vec,
            profile_embedding=vec,
        )
        assert any("高度" in r for r in reasons)

    def test_reasons_moderate_similarity_label(self):
        # Create a vector with cosine ~0.45 to the reference
        ref = _unit_vec(1.0, 0.0, 0.0)
        moderate = _unit_vec(0.45, 0.89, 0.0)  # dot ≈ 0.45
        matcher = self._make_matcher()
        _, reasons = matcher.match(
            profile={},
            professor={"research_interests": ["computer vision"]},
            professor_embedding=moderate.tolist(),
            profile_embedding=ref.tolist(),
        )
        assert any("较好" in r for r in reasons)

    def test_on_the_fly_encoding_does_not_crash(self):
        """When no cached embeddings are provided, the model is called.
        We mock the model to avoid downloading it in tests.
        """
        fake_vec = _unit_vec(1.0, 0.0, 0.0)
        fake_model = MagicMock()
        fake_model.encode.return_value = np.array([fake_vec])

        with patch(
            "prof_finder.matcher.semantic_matcher._model", fake_model
        ):
            matcher = SemanticMatcher()
            score, reasons = matcher.match(
                profile={"skills": ["NLP"]},
                professor={"research_interests": ["NLP"]},
            )
        assert 0.0 <= score <= 100.0
        assert len(reasons) > 0
