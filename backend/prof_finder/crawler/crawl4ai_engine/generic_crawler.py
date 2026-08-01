"""Generic university crawler driven by configuration.

Uses either CSS selectors or LLM extraction (depending on config) to crawl
professor list pages for any university.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from ...utils.url_utils import normalize_school_crawl_professors, resolve_absolute_url
from .css_extractor import extract_professors_css
from .llm_extractor import extract_professors_llm
from .profile_extractor import enrich_profiles_for_batch

logger = logging.getLogger(__name__)


class GenericUniversityCrawler:
    """Crawler that uses a configuration dict to crawl any university's faculty page.

    This can be used with either a database-backed UniversityCrawlerConfig
    row or an ad-hoc configuration dict (e.g. from a test-crawl request).
    """

    def __init__(
        self,
        university_id: str,
        display_name: str,
        list_url: str,
        extraction_mode: str = "css",
        css_selectors: Optional[dict] = None,
        affiliation: str = "",
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ):
        """Initialize the generic crawler.

        Args:
            university_id: Unique identifier for this crawler.
            display_name: Human-readable name (e.g. "Stanford CS").
            list_url: URL of the professor list page.
            extraction_mode: "css" or "llm".
            css_selectors: CSS selector config dict (required if mode is "css").
            affiliation: Affiliation string to assign to professors.
            api_key: LLM API key (for LLM mode).
            base_url: LLM API base URL (for LLM mode).
            model: LLM model name (for LLM mode).
            llm_provider: ``openai`` (OpenAI-compatible) or ``anthropic``.
        """
        self.university_id = university_id
        self.display_name = display_name
        self.list_url = list_url
        self.extraction_mode = extraction_mode
        self.css_selectors = css_selectors or {}
        self.affiliation = affiliation
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.llm_provider = llm_provider

    def crawl_all(
        self,
        *,
        delay: float = 2.0,
        send_progress: Optional[Callable[[str], None]] = None,
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> list[dict]:
        """Crawl all professors using the configured extraction mode.

        Args:
            delay: Seconds between page fetches (CSS mode only).
            send_progress: Optional callback for progress messages.
            cancel_checker: Optional callback returning True to abort.

        Returns:
            List of professor dicts with keys: name, affiliation, email,
            homepage, research_interests, url, title, photo_url.
        """
        if cancel_checker and cancel_checker():
            return []

        affiliation = self.affiliation or self.display_name

        if self.extraction_mode == "css":
            raw_results = extract_professors_css(
                self.list_url,
                self.css_selectors,
                affiliation,
                delay=delay,
                send_progress=send_progress,
                cancel_checker=cancel_checker,
            )
        elif self.extraction_mode == "llm":
            raw_results = extract_professors_llm(
                self.list_url,
                affiliation,
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                llm_provider=self.llm_provider,
                send_progress=send_progress,
                cancel_checker=cancel_checker,
            )
        else:
            logger.error("Unknown extraction mode: %s", self.extraction_mode)
            return []

        normalized = self._normalize_results(raw_results)
        if not normalized:
            return normalized

        normalize_school_crawl_professors(normalized, self.list_url)

        return enrich_profiles_for_batch(
            normalized,
            delay=delay,
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            llm_provider=self.llm_provider,
            page_base_url=self.list_url,
            send_progress=send_progress,
            cancel_checker=cancel_checker,
        )

    def _normalize_results(self, raw: list[dict]) -> list[dict]:
        """Normalize raw extraction results to a consistent format."""
        normalized: list[dict] = []
        for item in raw:
            raw_homepage = (item.get("homepage") or item.get("url") or "").strip()
            homepage = (
                resolve_absolute_url(raw_homepage, self.list_url)
                if raw_homepage
                else None
            )
            prof: dict = {
                "name": item.get("name", "").strip(),
                "affiliation": item.get("affiliation", self.affiliation or self.display_name),
                "email": item.get("email"),
                "homepage": homepage,
                "research_interests": item.get("research_interests") or [],
                "title": item.get("title"),
                "photo_url": item.get("photo_url"),
            }
            if prof["name"]:
                normalized.append(prof)
        return normalized

    @classmethod
    def from_db_config(
        cls,
        config_row,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> GenericUniversityCrawler:
        """Create a crawler from a UniversityCrawlerConfig database row.

        Args:
            config_row: UniversityCrawlerConfig SQLAlchemy model instance.
            api_key: DeepSeek API key for LLM mode.
            base_url: DeepSeek base URL for LLM mode.
            model: LLM model name for LLM mode.
        """
        return cls(
            university_id=f"custom-{config_row.id}",
            display_name=config_row.name,
            list_url=config_row.list_url,
            extraction_mode=config_row.extraction_mode,
            css_selectors=config_row.css_selectors or {},
            affiliation=config_row.affiliation or config_row.university,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    @classmethod
    def from_dict(cls, data: dict) -> GenericUniversityCrawler:
        """Create a crawler from a dict (e.g. API request body).

        Args:
            data: Dict with keys: list_url, extraction_mode, css_selectors,
                  affiliation, name, university, department.
        """
        name = data.get("name", "Custom")
        university = data.get("university", "")
        display_name = f"{university} {data.get('department', '')}".strip() or name

        return cls(
            university_id="test-crawl",
            display_name=display_name,
            list_url=data["list_url"],
            extraction_mode=data.get("extraction_mode", "css"),
            css_selectors=data.get("css_selectors") or {},
            affiliation=data.get("affiliation") or university,
        )
