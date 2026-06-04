"""Tests for professor duplicate detection helpers."""

from prof_finder.utils.professor_dedup import (
    affiliations_same_university,
    find_name_collision_groups,
    names_match,
)


class TestAffiliationsSameUniversity:
    def test_exact_match(self):
        assert affiliations_same_university("西安交通大学", "西安交通大学")

    def test_variant_match(self):
        variants = ["XJTU", "Xi'an Jiaotong University", "西安交大", "西交"]
        assert affiliations_same_university(
            "西安交通大学计算机科学与技术学院",
            "西安交大计算机学院",
            university_variants=variants,
            university_full_name="西安交通大学",
        )

    def test_different_universities(self):
        variants = ["XJTU", "西安交大"]
        assert not affiliations_same_university(
            "清华大学计算机系",
            "西安交大计算机学院",
            university_variants=variants,
            university_full_name="西安交通大学",
        )


class TestNamesMatch:
    def test_chinese_exact(self):
        assert names_match("张伟", "张伟")

    def test_chinese_and_pinyin(self):
        assert names_match("张伟", "Zhang, Wei")
        assert names_match("Zhang Wei", "张伟")


class TestNameCollisionGroups:
    def test_groups_same_name_same_uni_variants(self):
        class P:
            def __init__(self, id, name, affiliation):
                self.id = id
                self.name = name
                self.affiliation = affiliation

        class U:
            def __init__(self, full_name, name_variants):
                self.full_name = full_name
                self.name_variants = name_variants

        professors = [
            P(1, "李明", "西安交通大学软件学院"),
            P(2, "李明", "西安交大软件工程学院"),
            P(3, "王芳", "北京大学"),
        ]
        universities = [
            U(
                "西安交通大学",
                ["XJTU", "Xi'an Jiaotong University", "西安交大"],
            )
        ]
        groups = find_name_collision_groups(professors, universities)
        assert len(groups) == 1
        assert set(groups[0]["professor_ids"]) == {1, 2}
