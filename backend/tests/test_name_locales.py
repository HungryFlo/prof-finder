"""Tests for name_locales merge utilities."""

from types import SimpleNamespace

from prof_finder.utils.name_locales import (
    apply_dblp_name_update,
    apply_scholar_name_update,
    classify_name_locale,
    infer_locales_from_name,
    merge_name_locales,
    normalize_english_name,
)


def test_classify_name_locale():
    assert classify_name_locale("张伟") == "zh"
    assert classify_name_locale("Wei Zhang") == "en"
    assert classify_name_locale("") is None


def test_normalize_english_name():
    assert normalize_english_name("Zhang, Wei") == "Zhang Wei"
    assert normalize_english_name("  John   Doe  ") == "John Doe"


def test_infer_locales_from_name():
    assert infer_locales_from_name("李明") == {"zh": "李明"}
    assert infer_locales_from_name("Alice Smith") == {"en": "Alice Smith"}


def test_merge_fills_empty_only():
    prof = SimpleNamespace(name_locales={})
    assert merge_name_locales(prof, zh="王五", en="Wu Wang") is True
    assert prof.name_locales == {"zh": "王五", "en": "Wu Wang"}

    assert merge_name_locales(prof, zh="其他", en="Other Name") is False
    assert prof.name_locales["zh"] == "王五"
    assert prof.name_locales["en"] == "Wu Wang"


def test_merge_rejects_wrong_script():
    prof = SimpleNamespace(name_locales={})
    assert merge_name_locales(prof, en="张三") is False
    assert merge_name_locales(prof, zh="John Doe") is False
    assert prof.name_locales == {}


def test_merge_preserves_user_zh():
    prof = SimpleNamespace(name_locales={"zh": "用户填写"})
    merge_name_locales(prof, zh="爬虫名", en="Crawler Name")
    assert prof.name_locales["zh"] == "用户填写"
    assert prof.name_locales["en"] == "Crawler Name"


def test_apply_scholar_name_update_keeps_existing_display_name():
    prof = SimpleNamespace(name="黄俊锡", name_locales={})
    apply_scholar_name_update(prof, "Junxi Huang")
    assert prof.name == "黄俊锡"
    assert prof.name_locales.get("zh") == "黄俊锡"
    assert prof.name_locales.get("en") == "Junxi Huang"


def test_apply_dblp_name_update_fills_name_when_empty():
    prof = SimpleNamespace(name="", name_locales={})
    apply_dblp_name_update(prof, "Junxi Huang")
    assert prof.name == "Junxi Huang"
    assert prof.name_locales.get("en") == "Junxi Huang"


def test_apply_dblp_name_update_keeps_existing_display_name():
    prof = SimpleNamespace(name="黄俊锡", name_locales={})
    apply_dblp_name_update(prof, "Junxi Huang")
    assert prof.name == "黄俊锡"
    assert prof.name_locales.get("en") == "Junxi Huang"


def test_merge_normalizes_english_comma_form():
    prof = SimpleNamespace(name_locales={})
    merge_name_locales(prof, en="Zhang, Wei")
    assert prof.name_locales["en"] == "Zhang Wei"
