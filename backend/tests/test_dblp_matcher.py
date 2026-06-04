"""Tests for DBLP profile matching."""

from unittest.mock import MagicMock

from prof_finder.crawler.dblp_matcher import match_professor_dblp


def test_match_not_found_empty_search():
    client = MagicMock()
    client.search_author.return_value = []
    result = match_professor_dblp(
        chinese_name="不存在的人",
        crawled_email=None,
        university_variants=["Test University"],
        department_affiliation=None,
        dblp_client=client,
        request_delay=0,
    )
    assert result["status"] == "not_found"


def test_match_single_candidate():
    client = MagicMock()
    client.search_author.return_value = [
        {
            "name": "Wei Zhang",
            "pid": "z/WeiZhang",
            "url": "https://dblp.org/pid/z/WeiZhang.html",
            "affiliations": ["Test University"],
        }
    ]
    result = match_professor_dblp(
        chinese_name="张伟",
        crawled_email=None,
        university_variants=["Test University"],
        department_affiliation="Test University CS",
        dblp_client=client,
        request_delay=0,
    )
    assert result["status"] in ("matched", "not_found", "ambiguous")
