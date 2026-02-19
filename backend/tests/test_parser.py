"""Tests for resume parsers."""

import pytest
from prof_finder.parser import MarkdownParser, LaTeXParser


class TestMarkdownParser:
    """Tests for MarkdownParser."""

    def test_supported_extensions(self):
        assert ".md" in MarkdownParser.supported_extensions()
        assert ".markdown" in MarkdownParser.supported_extensions()

    def test_parse_simple_resume(self):
        content = """# 张三

## 教育背景
- 本科：清华大学 计算机科学 (2018-2022)
- 硕士：斯坦福大学 人工智能 (2022-2024)

## 科研经历
- **NLP研究助理** @ ABC实验室
  在NLP领域发表3篇论文，参与机器翻译项目

## 项目
- 智能对话系统
- 自然语言处理工具

## 技能
Python, TensorFlow, NLP算法, PyTorch
"""
        parser = MarkdownParser()
        result = parser.parse(content)

        assert result.name == "张三"
        assert len(result.education) >= 1
        assert len(result.research_experience) >= 1
        assert len(result.skills) >= 3
        assert "Python" in result.skills

    def test_parse_english_resume(self):
        content = """# John Smith

## Education
- Bachelor: MIT Computer Science (2018-2022)
- Master: Stanford AI (2022-2024)

## Research Experience
- Research Assistant @ NLP Lab
  Published papers in NLP, worked on machine translation

## Skills
Python, TensorFlow, Deep Learning
"""
        parser = MarkdownParser()
        result = parser.parse(content)

        assert result.name == "John Smith"
        assert len(result.education) >= 1
        assert "Python" in result.skills

    def test_parse_empty_content(self):
        parser = MarkdownParser()
        result = parser.parse("")
        
        assert result.is_empty()


class TestLaTeXParser:
    """Tests for LaTeXParser."""

    def test_supported_extensions(self):
        assert ".tex" in LaTeXParser.supported_extensions()
        assert ".latex" in LaTeXParser.supported_extensions()

    def test_parse_simple_latex(self):
        content = r"""
\documentclass{article}
\begin{document}

\name{李明}

\section{Education}
\begin{itemize}
\item Bachelor: Tsinghua University (2018-2022)
\item Master: Stanford University (2022-2024)
\end{itemize}

\section{Skills}
Python, TensorFlow, Machine Learning

\end{document}
"""
        parser = LaTeXParser()
        result = parser.parse(content)

        assert result.name is not None
        assert result.raw_content == content

    def test_latex_to_text_conversion(self):
        parser = LaTeXParser()
        
        # Test textbf removal
        text = parser._latex_to_text(r"\textbf{bold text}")
        assert "bold text" in text
        assert r"\textbf" not in text

        # Test href handling
        text = parser._latex_to_text(r"\href{http://example.com}{Link Text}")
        assert "Link Text" in text


class TestParserIntegration:
    """Integration tests for parsers."""

    def test_markdown_to_dict(self):
        content = """# Test
## Skills
Python, Java
"""
        parser = MarkdownParser()
        result = parser.parse(content)
        
        data = result.to_dict()
        assert "skills" in data
        assert isinstance(data["skills"], list)
