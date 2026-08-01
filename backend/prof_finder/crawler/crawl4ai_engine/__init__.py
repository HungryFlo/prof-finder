"""crawl4ai engine package — async crawler bridge and CSS/LLM extraction for university sites."""

from .css_extractor import extract_professors_css
from .engine import CrawlResult, crawl_url, crawl_url_full
from .generic_crawler import GenericUniversityCrawler
from .llm_extractor import extract_professors_llm
from .profile_extractor import enrich_profiles_for_batch, extract_professor_profile

__all__ = [
    "crawl_url",
    "crawl_url_full",
    "CrawlResult",
    "extract_professors_css",
    "extract_professors_llm",
    "extract_professor_profile",
    "enrich_profiles_for_batch",
    "GenericUniversityCrawler",
]
