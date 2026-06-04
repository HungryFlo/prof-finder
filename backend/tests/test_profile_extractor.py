"""Tests for single-profile crawl4ai + LLM extraction."""

from unittest.mock import MagicMock, patch

from prof_finder.crawler.crawl4ai_engine.engine import CrawlResult
from prof_finder.crawler.crawl4ai_engine.profile_extractor import (
    _parse_llm_json_object,
    enrich_profiles_for_batch,
    extract_professor_profile,
)


def test_parse_llm_json_object_strips_fences():
    raw = '```json\n{"email":"a@x.edu","research_interests":["ML"]}\n```'
    parsed = _parse_llm_json_object(raw)
    assert parsed["email"] == "a@x.edu"
    assert parsed["research_interests"] == ["ML"]


@patch("prof_finder.crawler.crawl4ai_engine.profile_extractor._llm_extract_profile")
@patch("prof_finder.crawler.crawl4ai_engine.profile_extractor._choose_best_content")
@patch("prof_finder.crawler.crawl4ai_engine.profile_extractor._try_ajax_endpoints")
@patch("prof_finder.crawler.crawl4ai_engine.profile_extractor.crawl_url_full")
def test_extract_professor_profile_success(mock_crawl, mock_ajax, mock_choose, mock_llm):
    mock_crawl.return_value = CrawlResult(
        success=True,
        html="<div>profile</div>",
        markdown="md",
    )
    mock_ajax.return_value = ""
    mock_choose.return_value = "<div>profile</div>"
    mock_llm.return_value = {
        "email": "prof@edu.cn",
        "research_interests": ["AI"],
        "bio": "Bio text",
    }

    result = extract_professor_profile(
        "https://example.edu/p1",
        name="Test Prof",
        affiliation="Test U",
        api_key="key",
    )
    assert result["email"] == "prof@edu.cn"
    mock_crawl.assert_called_once()


@patch("prof_finder.crawler.crawl4ai_engine.profile_extractor.extract_professor_profile")
def test_enrich_profiles_for_batch_continues_on_failure(mock_extract):
    mock_extract.side_effect = [
        {"email": "a@edu.cn", "research_interests": ["X"]},
        Exception("network error"),
    ]
    profs = [
        {"name": "A", "homepage": "https://a.edu"},
        {"name": "B", "homepage": "https://b.edu"},
    ]
    out = enrich_profiles_for_batch(profs, delay=0, api_key="k")
    assert out[0]["email"] == "a@edu.cn"
    assert "email" not in out[1] or out[1].get("email") is None


@patch("prof_finder.crawler.crawl4ai_engine.profile_extractor.crawl_url_full")
def test_extract_professor_profile_crawl_failure(mock_crawl):
    mock_crawl.return_value = CrawlResult(success=False, html="", markdown="")
    assert extract_professor_profile("https://bad.example") == {}
