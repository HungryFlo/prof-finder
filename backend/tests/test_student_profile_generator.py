"""Unit tests for StudentProfileGenerator JSON parsing helpers."""

from prof_finder.llm.student_profile_generator import StudentProfileGenerator


def test_parse_analysis_json_strips_markdown_fence():
    raw = """Here is the JSON:
```json
{"academic_positioning": "test", "gaps": []}
```
"""
    d = StudentProfileGenerator._parse_analysis_json(raw)
    assert d.get("academic_positioning") == "test"
    assert d.get("gaps") == []


def test_parse_analysis_json_fixes_trailing_comma():
    raw = '{"academic_positioning": "x", "gaps": ["a",],}'
    d = StudentProfileGenerator._parse_analysis_json(raw)
    assert d["academic_positioning"] == "x"
    assert d["gaps"] == ["a"]


def test_parse_analysis_json_balanced_brace_ignores_trailing_junk():
    raw = """Prefix
{"academic_positioning": "ok", "research_interests": []}
trailing explanation
"""
    d = StudentProfileGenerator._parse_analysis_json(raw)
    assert d.get("academic_positioning") == "ok"
