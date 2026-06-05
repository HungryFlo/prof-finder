"""Smart parser with LLM-first strategy and regex fallback."""

import logging
from typing import Optional, Tuple

from .base import BaseParser, ParsedResume
from ..ai_workflows.provider import LLMProvider
from .llm_parser import LLMParser, LLMParserError
from .latex_parser import LaTeXParser
from .markdown_parser import MarkdownParser


logger = logging.getLogger(__name__)


class SmartParser:
    """Smart parser that tries LLM first, then falls back to regex parsers.
    
    This parser provides the best of both worlds:
    - LLM parsing for high accuracy and semantic understanding
    - Regex parsing as a reliable offline fallback
    """

    def __init__(
        self,
        prefer_llm: bool = True,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """Initialize the smart parser.
        
        Args:
            prefer_llm: If True, try LLM parsing first. If False, use regex only.
            llm_provider: Optional pre-configured LLM provider (e.g. per-user settings).
        """
        self.prefer_llm = prefer_llm
        self._llm_provider = llm_provider
        self._llm_parser: Optional[LLMParser] = None
        self._latex_parser = LaTeXParser()
        self._markdown_parser = MarkdownParser()

    @property
    def llm_parser(self) -> Optional[LLMParser]:
        """Lazy initialization of LLM parser."""
        if self._llm_parser is None and self.prefer_llm:
            try:
                self._llm_parser = LLMParser(provider=self._llm_provider)
            except Exception as e:
                # Any initialization failure should gracefully fall back to regex parser.
                logger.warning(f"Could not initialize LLM parser: {e}")
        return self._llm_parser

    def parse(
        self,
        content: str,
        file_extension: str = ".md",
    ) -> Tuple[ParsedResume, str]:
        """Parse resume content using the best available method.
        
        Args:
            content: Raw resume content string.
            file_extension: File extension to determine fallback parser.
            
        Returns:
            Tuple of (ParsedResume, method_used) where method_used is
            "llm" or "regex".
        """
        if not content.strip():
            return ParsedResume(raw_content=content), "empty"

        # Try LLM parsing first if enabled
        if self.prefer_llm and self.llm_parser:
            try:
                result = self.llm_parser.parse(content)
                if not result.is_empty():
                    return result, "llm"
                logger.info("LLM parsing returned empty result, falling back to regex")
            except LLMParserError as e:
                logger.warning(f"LLM parsing failed: {e}, falling back to regex")
            except Exception as e:
                logger.warning(f"Unexpected error in LLM parsing: {e}, falling back to regex")

        # Fall back to regex parser
        return self._parse_with_regex(content, file_extension), "regex"

    def _parse_with_regex(self, content: str, file_extension: str) -> ParsedResume:
        """Parse using the appropriate regex parser.
        
        Args:
            content: Raw resume content string.
            file_extension: File extension to determine parser.
            
        Returns:
            ParsedResume with extracted data.
        """
        ext = file_extension.lower()
        
        if ext in self._latex_parser.supported_extensions():
            return self._latex_parser.parse(content)
        elif ext in self._markdown_parser.supported_extensions():
            return self._markdown_parser.parse(content)
        else:
            # Default to markdown parser for unknown extensions
            logger.info(f"Unknown extension {ext}, using markdown parser")
            return self._markdown_parser.parse(content)

    def parse_file(
        self,
        file_path: str,
    ) -> Tuple[ParsedResume, str]:
        """Parse resume from file.
        
        Args:
            file_path: Path to resume file.
            
        Returns:
            Tuple of (ParsedResume, method_used).
        """
        from pathlib import Path
        
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return self.parse(content, path.suffix)
