"""Tests for source_input_service helpers."""

from prof_finder.api.source_input_service import keep_non_scholar_paper_summaries


def test_keep_non_scholar_paper_summaries_drops_scholar_pub_only():
    merged = keep_non_scholar_paper_summaries(
        [
            {"source_type": "scholar_pub", "title": "S1"},
            {"source_type": "arxiv", "title": "A1", "source_input_id": 3},
            {"title": "legacy"},
        ]
    )
    assert len(merged) == 2
    assert merged[0]["source_type"] == "arxiv"
    assert "legacy" == merged[1]["title"]


def test_keep_non_scholar_paper_summaries_empty():
    assert keep_non_scholar_paper_summaries(None) == []
    assert keep_non_scholar_paper_summaries([]) == []
