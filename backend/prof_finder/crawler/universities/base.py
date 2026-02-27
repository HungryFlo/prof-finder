"""Abstract base class for university-specific professor crawlers."""

from abc import ABC, abstractmethod


class UniversityCrawlerBase(ABC):
    """Base class for crawling professor lists from university department websites.

    Each university's HTML structure is different, so each implementation lives in
    its own file. All crawlers expose a unified interface for the task manager.

    Attributes:
        university_id: Unique kebab-case identifier (e.g. "xjtu-cs").
        display_name: Human-readable name shown in the UI (e.g. "西安交通大学 - 计算机科学与技术学院").
    """

    university_id: str
    display_name: str

    @abstractmethod
    def crawl_all(self, delay: float = 2.0) -> list[dict]:
        """Crawl the department's professor list page and all individual detail pages.

        Args:
            delay: Seconds to wait between HTTP requests.

        Returns:
            List of professor dicts with keys:
                - name (str): Full name.
                - affiliation (str): University + department string.
                - source_url (str): URL of the professor's detail page.
                - email (str | None): Contact email, if found.
                - homepage (str | None): Personal or lab homepage, if found.
                - research_interests (list[str]): Research interest keywords.

        Raises:
            RuntimeError: If the list page is unreachable or returns non-200 status.
        """
