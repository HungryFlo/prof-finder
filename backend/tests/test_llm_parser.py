"""Tests for LLM resume parser and prompt management."""

import json
import pytest
from unittest.mock import MagicMock, patch

from prof_finder.parser import LLMParser, LLMParserError, SmartParser
from prof_finder.parser.base import ParsedResume
from prof_finder.prompts import get_prompt, load_prompt_file, clear_cache


class TestPromptManagement:
    """Tests for prompt loading and management."""

    def test_load_prompt_file(self):
        """Test loading a prompt YAML file."""
        prompts = load_prompt_file("resume_parser")
        assert "resume_extraction" in prompts
        assert "system" in prompts["resume_extraction"]
        assert "user" in prompts["resume_extraction"]

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_prompt_file("nonexistent_file")

    def test_get_prompt_with_part(self):
        """Test getting a specific part of a prompt."""
        system_prompt = get_prompt("resume_parser", "resume_extraction", "system")
        assert "简历解析助手" in system_prompt or "JSON" in system_prompt

    def test_get_prompt_with_variables(self):
        """Test variable substitution in prompts."""
        user_prompt = get_prompt(
            "resume_parser",
            "resume_extraction",
            "user",
            content="Test resume content"
        )
        assert "Test resume content" in user_prompt

    def test_get_prompt_missing_key(self):
        """Test getting a non-existent prompt raises error."""
        with pytest.raises(KeyError):
            get_prompt("resume_parser", "nonexistent_prompt", "system")

    def test_cache_clear(self):
        """Test cache clearing works."""
        # Load once to populate cache
        load_prompt_file("resume_parser")
        # Clear cache
        clear_cache()
        # Should work again (will reload)
        prompts = load_prompt_file("resume_parser")
        assert prompts is not None


class TestLLMParser:
    """Tests for LLMParser."""

    @pytest.fixture
    def mock_llm_response(self):
        """Sample LLM response."""
        return json.dumps({
            "name": "张三",
            "education": [
                {
                    "degree": "本科",
                    "school": "清华大学",
                    "major": "计算机科学",
                    "period": "2018-2022"
                }
            ],
            "research_experience": [
                {
                    "title": "研究助理",
                    "organization": "NLP实验室",
                    "description": "参与机器翻译项目",
                    "period": "2021-2022"
                }
            ],
            "projects": [
                {
                    "name": "智能对话系统",
                    "description": "基于Transformer的对话系统"
                }
            ],
            "skills": ["Python", "PyTorch", "NLP"]
        })

    def test_parse_success(self, mock_llm_response):
        """Test successful LLM parsing."""
        mock_provider = MagicMock()
        mock_provider.enabled = True
        mock_provider.chat_completion.return_value = mock_llm_response

        parser = LLMParser(provider=mock_provider)
        result = parser.parse("Test resume content")

        assert result.name == "张三"
        assert len(result.education) == 1
        assert result.education[0].school == "清华大学"
        assert len(result.skills) == 3
        assert "Python" in result.skills

    def test_parse_json_in_code_block(self, mock_llm_response):
        """Test parsing JSON wrapped in markdown code block."""
        response_with_block = f"```json\n{mock_llm_response}\n```"
        mock_provider = MagicMock()
        mock_provider.enabled = True
        mock_provider.chat_completion.return_value = response_with_block

        parser = LLMParser(provider=mock_provider)
        result = parser.parse("Test resume content")

        assert result.name == "张三"

    def test_parse_api_error_raises(self):
        """Test that API errors raise LLMParserError."""
        mock_provider = MagicMock()
        mock_provider.enabled = True
        mock_provider.chat_completion.side_effect = Exception("API Error")

        parser = LLMParser(provider=mock_provider)
        with pytest.raises(LLMParserError):
            parser.parse("Test content")

    def test_missing_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        mock_provider = MagicMock()
        mock_provider.enabled = False

        with pytest.raises(ValueError, match="LLM API Key"):
            LLMParser(provider=mock_provider)

    def test_parse_empty_content_raises(self):
        """Test that empty content raises error."""
        mock_provider = MagicMock()
        mock_provider.enabled = True

        parser = LLMParser(provider=mock_provider)
        with pytest.raises(LLMParserError, match="Empty"):
            parser.parse("")


class TestSmartParser:
    """Tests for SmartParser with fallback logic."""

    @patch("prof_finder.parser.smart_parser.LLMParser")
    def test_llm_first_strategy(self, mock_llm_parser_class):
        """Test that LLM is tried first when enabled."""
        mock_parser = MagicMock()
        mock_llm_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = ParsedResume(name="Test", raw_content="content")

        smart = SmartParser(prefer_llm=True)
        result, method = smart.parse("Test content", ".md")

        assert method == "llm"
        assert result.name == "Test"
        mock_parser.parse.assert_called_once()

    @patch("prof_finder.parser.smart_parser.LLMParser")
    def test_fallback_on_llm_error(self, mock_llm_parser_class):
        """Test fallback to regex when LLM fails."""
        mock_parser = MagicMock()
        mock_llm_parser_class.return_value = mock_parser
        mock_parser.parse.side_effect = LLMParserError("Test error")

        content = """# Test Name
## Skills
Python, Java
"""
        smart = SmartParser(prefer_llm=True)
        result, method = smart.parse(content, ".md")

        assert method == "regex"
        assert "Python" in result.skills

    @patch("prof_finder.parser.smart_parser.LLMParser")
    def test_fallback_when_llm_init_unexpected_error(self, mock_llm_parser_class):
        """Test fallback to regex when LLM parser initialization raises non-ValueError."""
        mock_llm_parser_class.side_effect = RuntimeError("init failed")

        content = r"""
\section{Skills}
Python, TensorFlow
"""
        smart = SmartParser(prefer_llm=True)
        result, method = smart.parse(content, ".tex")

        assert method == "regex"
        assert "Python" in result.skills

    def test_regex_only_mode(self):
        """Test regex-only mode skips LLM."""
        content = """# Test Name
## Skills
Python, Java
"""
        smart = SmartParser(prefer_llm=False)
        result, method = smart.parse(content, ".md")

        assert method == "regex"
        assert "Python" in result.skills

    def test_correct_parser_for_latex(self):
        """Test correct regex parser selected for LaTeX."""
        content = r"""
\section{Skills}
Python, TensorFlow
"""
        smart = SmartParser(prefer_llm=False)
        result, method = smart.parse(content, ".tex")

        assert method == "regex"

    def test_empty_content_returns_empty(self):
        """Test empty content handling."""
        smart = SmartParser(prefer_llm=False)
        result, method = smart.parse("", ".md")

        assert method == "empty"
        assert result.is_empty()
