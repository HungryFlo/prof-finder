"""Tests for profile field merge utilities."""

from prof_finder.utils.profile_merge import (
    apply_external_affiliation,
    merge_external_affiliation,
    merge_profile_fields,
    merge_profile_into_dict,
)


def test_merge_email_fill_empty():
    merged = merge_profile_fields(email=None, extracted={"email": "a@edu.cn"})
    assert merged["email"] == "a@edu.cn"


def test_merge_email_keep_existing_on_conflict():
    merged = merge_profile_fields(
        email="keep@edu.cn",
        extracted={"email": "new@edu.cn"},
    )
    assert merged["email"] == "keep@edu.cn"
    assert "爬取邮箱: new@edu.cn" in (merged["manual_notes"] or "")


def test_merge_interests_union():
    merged = merge_profile_fields(
        research_interests=["NLP"],
        extracted={"research_interests": ["CV", "nlp"]},
    )
    assert merged["research_interests"] == ["NLP", "CV"]


def test_merge_bio_and_external_homepage_to_notes():
    merged = merge_profile_fields(
        homepage="https://dept.edu/teacher/foo",
        extracted={
            "bio": "研究方向广泛",
            "external_homepage": "https://personal.edu/~foo",
        },
    )
    notes = merged["manual_notes"] or ""
    assert "研究方向广泛" in notes
    assert "外部主页: https://personal.edu/~foo" in notes
    assert merged["homepage"] == "https://dept.edu/teacher/foo"


def test_merge_external_affiliation_keeps_existing():
    assert merge_external_affiliation("西安交通大学", "MIT") == "西安交通大学"


def test_merge_external_affiliation_fills_when_empty():
    assert merge_external_affiliation(None, "MIT") == "MIT"
    assert merge_external_affiliation("  ", "MIT") == "MIT"


def test_apply_external_affiliation_on_mock_professor():
    class Prof:
        affiliation = "已有学校"

    p = Prof()
    apply_external_affiliation(p, "DBLP University")
    assert p.affiliation == "已有学校"

    p.affiliation = None
    apply_external_affiliation(p, "DBLP University")
    assert p.affiliation == "DBLP University"


def test_merge_profile_into_dict():
    prof = {
        "name": "张三",
        "email": None,
        "research_interests": ["A"],
        "homepage": "https://example.edu/p1",
    }
    merge_profile_into_dict(
        prof,
        {"email": "z@edu.cn", "research_interests": ["B"], "title": "教授"},
    )
    assert prof["email"] == "z@edu.cn"
    assert prof["research_interests"] == ["A", "B"]
    assert "职称: 教授" in prof["manual_notes"]
