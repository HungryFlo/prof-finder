"""crawl4ai engine package — async crawler bridge and CSS/LLM extraction for university sites."""

from .engine import crawl_url, crawl_url_full, CrawlResult
from .css_extractor import extract_professors_css
from .llm_extractor import extract_professors_llm
from .generic_crawler import GenericUniversityCrawler
from .profile_extractor import extract_professor_profile, enrich_profiles_for_batch

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
