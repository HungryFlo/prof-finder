"""crawl4ai engine package — async crawler bridge, CSS/LLM extraction, Scholar fallback."""

from .engine import crawl_url, crawl_url_full, CrawlResult
from .css_extractor import extract_professors_css
from .llm_extractor import extract_professors_llm
from .generic_crawler import GenericUniversityCrawler

__all__ = [
    "crawl_url",
    "crawl_url_full",
    "CrawlResult",
    "extract_professors_css",
    "extract_professors_llm",
    "GenericUniversityCrawler",
]
