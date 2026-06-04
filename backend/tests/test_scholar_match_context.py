"""Tests for scholar match context resolution."""

from prof_finder.models.schema import Professor, University
from prof_finder.utils.scholar_match_context import resolve_scholar_match_params


def test_resolve_prefers_university_matching_affiliation():
    prof = Professor(name="张伟", affiliation="西安交通大学计算机学院")
    uni = University(
        full_name="西安交通大学",
        name_variants=["XJTU", "Xi'an Jiaotong University", "西交"],
    )
    variants, dept = resolve_scholar_match_params(prof, [uni])
    assert variants == ["XJTU", "Xi'an Jiaotong University", "西交"]
    assert dept == "西安交通大学计算机学院"


def test_resolve_falls_back_to_affiliation_only():
    prof = Professor(name="John Smith", affiliation="MIT CSAIL")
    variants, dept = resolve_scholar_match_params(prof, [])
    assert variants == []
    assert dept == "MIT CSAIL"


def test_resolve_empty_without_affiliation_or_university():
    prof = Professor(name="张伟", affiliation=None)
    variants, dept = resolve_scholar_match_params(prof, [])
    assert variants == []
    assert dept is None
