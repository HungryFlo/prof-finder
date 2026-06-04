"""Tests for crawl URL resolution."""

from prof_finder.utils.url_utils import (
    normalize_school_crawl_professor,
    resolve_absolute_url,
)


def test_resolve_relative_path_against_list_page():
    base = "https://www.hku.hk/faculty/list"
    assert (
        resolve_absolute_url("/cris/rp/rp03608", base)
        == "https://www.hku.hk/cris/rp/rp03608"
    )


def test_resolve_leaves_absolute_unchanged():
    url = "https://example.edu/prof/1"
    assert resolve_absolute_url(url, "https://other.edu/list") == url


def test_resolve_empty_returns_empty():
    assert resolve_absolute_url("", "https://example.edu") == ""


def test_normalize_school_crawl_professor_homepage_and_url():
    prof = {"name": "Test", "homepage": "/cris/rp/rp03608", "url": "/other"}
    normalize_school_crawl_professor(prof, "https://www.hku.hk/faculty/list")
    assert prof["homepage"] == "https://www.hku.hk/cris/rp/rp03608"
    assert prof["url"] == "https://www.hku.hk/other"
