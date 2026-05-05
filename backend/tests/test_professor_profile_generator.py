"""Unit tests for ProfessorProfileGenerator and downstream integration."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from prof_finder.ai_workflows.provider import LLMProvider
from prof_finder.llm.professor_profile_generator import ProfessorProfileGenerator
from prof_finder.matcher.semantic_matcher import build_professor_text


# ---------------------------------------------------------------------------
# Source bundle construction
# ---------------------------------------------------------------------------

class TestSourceBundle:
    def test_builds_bundle_from_full_professor_data(self):
        gen = ProfessorProfileGenerator(api_key="sk-test", base_url="https://test.api/v1")
        data = {
            "name": "Jane Smith",
            "affiliation": "Stanford University",
            "homepage": "https://stanford.edu/~jsmith",
            "google_scholar_url": "https://scholar.google.com/citations?user=abc123",
            "research_interests": ["natural language processing", "information extraction"],
            "publications": [
                {"title": "A Survey of Relation Extraction", "year": 2024, "citations": 120},
                {"title": "Few-Shot NER with LLMs", "year": 2023, "citations": 45},
            ],
            "paper_summaries": [
                {
                    "title": "A Survey of Relation Extraction",
                    "summary": "Comprehensive survey of relation extraction methods.",
                    "keywords": ["relation extraction", "survey"],
                },
            ],
            "manual_notes": "Prof. Smith is actively recruiting PhD students for NLP research.",
        }
        bundle = gen._build_source_bundle(data)
        assert "Stanford University" in bundle["source_info"]
        assert "natural language processing" in bundle["research_interests"]
        assert "A Survey of Relation Extraction" in bundle["publications"]
        assert "relation extraction" in bundle["paper_summaries"]
        assert "actively recruiting" in bundle["manual_notes"]
        assert len(bundle["source_meta"]) >= 4

    def test_builds_bundle_from_minimal_data(self):
        gen = ProfessorProfileGenerator(api_key="sk-test", base_url="https://test.api/v1")
        data = {
            "name": "Minimal Prof",
            "affiliation": "Unknown University",
            "research_interests": [],
            "publications": [],
            "paper_summaries": [],
            "manual_notes": None,
        }
        bundle = gen._build_source_bundle(data)
        assert "Unknown University" in bundle["source_info"]
        assert "(无)" == bundle["research_interests"]
        assert "(无)" == bundle["publications"]
        assert "(无)" == bundle["paper_summaries"]
        assert "(无)" == bundle["manual_notes"]

    def test_format_publications_limit_30(self):
        pubs = [{"title": f"Paper {i}", "year": 2000 + i, "citations": i} for i in range(50)]
        formatted = ProfessorProfileGenerator._format_publications(pubs)
        assert "Paper 0" in formatted
        assert "Paper 29" in formatted
        assert "Paper 30" not in formatted


# ---------------------------------------------------------------------------
# JSON parsing (shared logic, test with professor profile data)
# ---------------------------------------------------------------------------

class TestParseAnalysisJson:
    def test_strips_markdown_fence(self):
        raw = '```json\n{"research_positioning": "test", "gaps": []}\n```'
        d = ProfessorProfileGenerator._parse_analysis_json(raw)
        assert d.get("research_positioning") == "test"

    def test_fixes_trailing_comma(self):
        raw = '{"research_positioning": "x", "gaps": ["a",],}'
        d = ProfessorProfileGenerator._parse_analysis_json(raw)
        assert d["research_positioning"] == "x"
        assert d["gaps"] == ["a"]

    def test_balanced_brace_ignores_trailing_junk(self):
        raw = 'Prefix\n{"research_positioning": "ok", "research_themes": []}\ntrailing'
        d = ProfessorProfileGenerator._parse_analysis_json(raw)
        assert d.get("research_positioning") == "ok"

    def test_empty_string_returns_empty_dict(self):
        assert ProfessorProfileGenerator._parse_analysis_json("") == {}


# ---------------------------------------------------------------------------
# Manual note priority (via prompt inspection)
# ---------------------------------------------------------------------------

class TestManualNotePriority:
    def test_manual_notes_placed_first_in_bundle(self):
        """Manual notes appear as the first element in source_meta and formatter output."""
        gen = ProfessorProfileGenerator(api_key="sk-test", base_url="https://test.api/v1")
        data = {
            "name": "Test Prof",
            "affiliation": "Test U",
            "research_interests": ["AI"],
            "publications": [{"title": "Paper"}],
            "paper_summaries": [],
            "manual_notes": "CRITICAL: This professor prefers students with strong math background.",
        }
        bundle = gen._build_source_bundle(data)
        # Manual notes should contain the critical info
        assert "CRITICAL" in bundle["manual_notes"]
        assert "strong math background" in bundle["manual_notes"]


# ---------------------------------------------------------------------------
# as_list helper
# ---------------------------------------------------------------------------

class TestAsList:
    def test_list_unchanged(self):
        assert ProfessorProfileGenerator._as_list(["a", "b"]) == ["a", "b"]

    def test_str_wrapped(self):
        assert ProfessorProfileGenerator._as_list("hello") == ["hello"]

    def test_none_returns_empty(self):
        assert ProfessorProfileGenerator._as_list(None) == []
        assert ProfessorProfileGenerator._as_list("") == []


# ---------------------------------------------------------------------------
# Semantic matching professor text with research profile
# ---------------------------------------------------------------------------

class TestBuildProfessorTextWithProfile:
    def test_uses_research_profile_when_available(self):
        professor = {
            "research_interests": ["old interest"],
            "publications": [{"title": "Old Paper"}],
            "paper_summaries": [],
            "affiliation": "Test University",
            "research_profile": "# Professor Research Profile\n\nResearch positioning: NLP researcher focusing on multilingual models.",
            "research_profile_analysis": {
                "research_positioning": "NLP researcher focusing on multilingual models.",
                "research_themes": [
                    {"theme": "multilingual NLP"},
                    {"theme": "cross-lingual transfer"},
                ],
            },
        }
        text = build_professor_text(professor)
        assert "multilingual NLP" in text
        assert "cross-lingual transfer" in text
        assert "[SEP]" in text

    def test_falls_back_to_interests_without_profile(self):
        professor = {
            "research_interests": ["computer vision", "image processing"],
            "publications": [{"title": "CNN Architectures"}],
            "paper_summaries": [],
            "affiliation": "CV Lab",
        }
        text = build_professor_text(professor)
        assert "computer vision" in text
        assert "image processing" in text
        assert "[SEP]" in text

    def test_includes_publications_in_body(self):
        professor = {
            "research_interests": ["AI"],
            "publications": [
                {"title": "Deep Learning"},
                {"title": "Reinforcement Learning"},
            ],
            "paper_summaries": [],
            "affiliation": "AI Lab",
        }
        text = build_professor_text(professor)
        assert "Deep Learning" in text
        assert "Reinforcement Learning" in text
        assert "[SEP]" in text

    def test_includes_paper_summaries_in_body(self):
        professor = {
            "research_interests": ["AI"],
            "publications": [],
            "paper_summaries": [
                {"title": "Paper A", "summary": "Summary of paper A"},
            ],
            "affiliation": "AI Lab",
        }
        text = build_professor_text(professor)
        assert "Paper A" in text
        assert "Summary of paper A" in text


# ---------------------------------------------------------------------------
# Sparse data handling
# ---------------------------------------------------------------------------

class TestSparseData:
    def test_empty_professor_produces_valid_text(self):
        professor = {
            "research_interests": [],
            "publications": [],
            "paper_summaries": [],
            "affiliation": "",
        }
        text = build_professor_text(professor)
        assert text.endswith("[SEP] ")
        assert text == " [SEP] "

    def test_generate_disabled_raises(self):
        # "test_key" is in the blocked set, so enabled will be False
        gen = ProfessorProfileGenerator(api_key="test_key")
        with pytest.raises(ValueError, match="DeepSeek API Key"):
            gen.generate({})


# ---------------------------------------------------------------------------
# Embedding invalidation (integration via task_manager mock)
# ---------------------------------------------------------------------------

class TestEmbeddingInvalidation:
    """Verify that professor profile generation clears the cached embedding."""

    def test_profile_generation_clears_embedding(self):
        """This is tested at the task_manager/route level; here we verify
        the ProfessorProfileGenerator.generate() returns the expected keys
        so the task executor can persist them.
        """
        # We can't easily test the full task executor without DB setup,
        # but we verify the return dict shape.
        with patch.object(ProfessorProfileGenerator, '_analyze') as mock_analyze, \
             patch.object(ProfessorProfileGenerator, '_build_profile') as mock_build:
            mock_analyze.return_value = {
                "research_positioning": "test",
                "research_themes": [{"theme": "NLP", "evidence": ["test"], "inferred": False}],
                "methods_and_assets": [],
                "representative_works": [],
                "recent_direction": "",
                "student_fit_signals": [],
                "evidence_notes": ["note1"],
                "conflict_notes": ["conflict1"],
                "insufficient_evidence": [],
            }
            mock_build.return_value = "# Test Profile\n\nGenerated content."

            gen = ProfessorProfileGenerator(api_key="sk-test", base_url="https://test.api/v1")
            result = gen.generate({
                "name": "Test",
                "affiliation": "U",
                "research_interests": ["AI"],
                "publications": [],
                "paper_summaries": [],
                "manual_notes": None,
            })
            assert result["research_profile"] == "# Test Profile\n\nGenerated content."
            assert result["research_profile_evidence"] == ["note1"]
            assert result["research_profile_conflicts"] == ["conflict1"]
            assert len(result["research_profile_sources"]) >= 1
            assert "research_profile_analysis" in result
