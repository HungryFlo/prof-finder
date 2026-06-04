"""Tests for publication merge utilities."""

from prof_finder.utils.publication_merge import merge_publications, normalize_title


def test_normalize_title_strips_punctuation():
    assert normalize_title("Hello, World!") == "hello world"


def test_merge_replaces_same_source():
    existing = [
        {"title": "Old DBLP Paper", "source": "dblp", "year": "2020"},
        {"title": "Scholar Paper", "source": "scholar", "citations": 5},
    ]
    incoming = [{"title": "New DBLP Paper", "year": "2024"}]
    merged = merge_publications(existing, incoming, "dblp")
    titles = {p["title"] for p in merged}
    assert "Old DBLP Paper" not in titles
    assert "New DBLP Paper" in titles
    assert "Scholar Paper" in titles


def test_merge_dedupes_cross_source_by_title():
    existing = [{"title": "Attention Is All You Need", "source": "scholar", "citations": 100}]
    incoming = [{"title": "Attention is All You Need", "year": "2017", "dblp_url": "https://dblp.org/rec/x"}]
    merged = merge_publications(existing, incoming, "dblp")
    assert len(merged) == 1
    assert merged[0].get("citations") == 100
