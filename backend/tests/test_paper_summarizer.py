"""Unit tests for paper summarizer."""

from prof_finder.llm.paper_summarizer import PaperSummarizer


def test_summarizer_fallback_without_api_key():
    summarizer = PaperSummarizer(api_key="")
    result = summarizer.summarize_with_fallback(
        source_type="pdf",
        title="Test Paper",
        content="This paper studies transformer language model methods for NLP tasks.",
    )
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert "keywords" in result
    assert isinstance(result["keywords"], list)


def test_parse_json_from_wrapped_content():
    payload = PaperSummarizer._safe_parse_json(
        "```json\n{\"summary\":\"abc\",\"keywords\":[\"nlp\"]}\n```"
    )
    assert payload["summary"] == "abc"
    assert payload["keywords"] == ["nlp"]
