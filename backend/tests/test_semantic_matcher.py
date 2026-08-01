"""Semantic matcher scoring and text serialisation.

These tests never load the embedding model: text builders are pure, and the
matcher is exercised with pre-computed vectors.
"""

from __future__ import annotations

import math

import pytest

from prof_finder.matcher.semantic_matcher import (
    SemanticMatcher,
    build_professor_text,
    build_profile_text,
)


def unit(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector]


class TestBuildProfessorText:
    def test_prefers_the_research_profile_over_interests(self):
        text = build_professor_text(
            {
                "research_profile": "Works on distributed databases",
                "research_interests": ["compilers"],
            }
        )
        assert "distributed databases" in text
        assert "compilers" not in text

    def test_falls_back_to_interests(self):
        text = build_professor_text({"research_interests": ["compilers", "type systems"]})
        assert text == "compilers; type systems"

    def test_includes_research_positioning_and_themes(self):
        text = build_professor_text(
            {
                "research_profile": "Profile body",
                "research_profile_analysis": {
                    "research_positioning": "Systems researcher",
                    "research_themes": [{"theme": "Consensus"}, {"theme": "Storage"}],
                },
            }
        )
        assert "Systems researcher" in text
        assert "Consensus" in text and "Storage" in text

    def test_appends_at_most_five_paper_summaries(self):
        text = build_professor_text(
            {
                "research_interests": ["ml"],
                "paper_summaries": [
                    {"title": f"Paper{i}", "summary": f"Summary{i}"} for i in range(8)
                ],
            }
        )
        assert "Paper4" in text
        assert "Paper5" not in text

    def test_empty_professor_yields_empty_text(self):
        assert build_professor_text({}) == ""


class TestBuildProfileText:
    def test_combines_skills_and_generated_profile(self):
        text = build_profile_text(
            {"skills": ["python", "pytorch"], "academic_profile": "Undergrad in CS"}
        )
        assert "python; pytorch" in text
        assert "Undergrad in CS" in text

    def test_includes_analysis_topics(self):
        text = build_profile_text(
            {
                "skills": [],
                "academic_profile": "Body",
                "profile_analysis": {
                    "academic_positioning": "Systems-leaning",
                    "research_interests": [{"topic": "Databases"}],
                    "target_directions": ["Storage engines"],
                },
            }
        )
        assert "Systems-leaning" in text
        assert "Databases" in text
        assert "Storage engines" in text

    def test_includes_experience_and_projects(self):
        text = build_profile_text(
            {
                "skills": ["c++"],
                "research_experience": [{"title": "Lab RA", "description": "Built a parser"}],
                "projects": [{"name": "Toy DB", "description": "LSM tree"}],
            }
        )
        assert "Lab RA" in text and "Built a parser" in text
        assert "Toy DB" in text and "LSM tree" in text

    def test_skills_only_profile(self):
        assert build_profile_text({"skills": ["rust"]}) == "rust"


class TestMatchScoring:
    def test_identical_vectors_score_100(self):
        vector = unit([1.0, 0.0, 0.0])
        score, _ = SemanticMatcher().match(
            {}, {}, professor_embedding=vector, profile_embedding=vector
        )
        assert score == pytest.approx(100.0)

    def test_orthogonal_vectors_score_50(self):
        score, _ = SemanticMatcher().match(
            {},
            {},
            professor_embedding=unit([1.0, 0.0]),
            profile_embedding=unit([0.0, 1.0]),
        )
        assert score == pytest.approx(50.0)

    def test_opposite_vectors_score_0(self):
        score, _ = SemanticMatcher().match(
            {},
            {},
            professor_embedding=[1.0, 0.0],
            profile_embedding=[-1.0, 0.0],
        )
        assert score == pytest.approx(0.0)

    def test_score_stays_within_bounds(self):
        for professor, profile in (([1.0, 0.0], [1.0, 0.0]), ([1.0, 0.0], [-1.0, 0.0])):
            score, _ = SemanticMatcher().match(
                {}, {}, professor_embedding=professor, profile_embedding=profile
            )
            assert 0.0 <= score <= 100.0

    def test_reasons_use_the_requested_language(self):
        vector = unit([1.0, 0.0])
        _, english = SemanticMatcher().match(
            {},
            {"research_interests": ["databases"]},
            professor_embedding=vector,
            profile_embedding=vector,
            language="en",
        )
        assert any("Strong semantic match" in reason for reason in english)

        _, chinese = SemanticMatcher().match(
            {},
            {"research_interests": ["数据库"]},
            professor_embedding=vector,
            profile_embedding=vector,
            language="zh",
        )
        assert any("语义高度匹配" in reason for reason in chinese)

    def test_unknown_language_falls_back_to_chinese(self):
        vector = unit([1.0, 0.0])
        _, reasons = SemanticMatcher().match(
            {}, {}, professor_embedding=vector, profile_embedding=vector, language="fr"
        )
        assert any("语义相似度" in reason for reason in reasons)


def test_batch_size_is_configurable(monkeypatch):
    from prof_finder.config import settings
    from prof_finder.matcher import semantic_matcher

    monkeypatch.setattr(settings, "embedding_batch_size", 16)
    assert semantic_matcher._batch_size() == 16


class TestScoreBatch:
    def test_matches_single_score_path(self):
        import numpy as np

        profile = unit([1.0, 0.0, 0.0])
        professors = [
            {"research_interests": ["a"]},
            {"research_interests": ["b"]},
        ]
        matrix = np.stack([unit([1.0, 0.0, 0.0]), unit([0.0, 1.0, 0.0])])
        batch = SemanticMatcher().score_batch(profile, matrix, professors, language="en")
        assert batch[0][0] == pytest.approx(100.0)
        assert batch[1][0] == pytest.approx(50.0)
        assert any("Strong semantic match" in reason for reason in batch[0][1])


class TestEmbeddingCodec:
    def test_roundtrip(self):
        import numpy as np

        from prof_finder.matcher.embedding_codec import pack_embedding, unpack_embedding

        vec = np.linspace(-1, 1, 1024, dtype=np.float32)
        packed = pack_embedding(vec)
        assert isinstance(packed, bytes)
        assert len(packed) == 4096
        restored = unpack_embedding(packed)
        assert restored is not None
        assert np.allclose(restored, vec)

    def test_rejects_wrong_length(self):
        import pytest as _pytest

        from prof_finder.matcher.embedding_codec import pack_embedding, unpack_embedding

        with _pytest.raises(ValueError):
            pack_embedding([0.0, 1.0])
        assert unpack_embedding(b"short") is None
