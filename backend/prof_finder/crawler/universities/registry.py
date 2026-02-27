"""Registry of all available university crawlers.

To add a new university crawler:
1. Create a new file in this directory (e.g. ``pku_cs.py``) implementing
   :class:`~.base.UniversityCrawlerBase`.
2. Import the class here and add an entry to ``REGISTRY``.
"""

from .base import UniversityCrawlerBase
from .xjtu_cs import XJTUCSCrawler

REGISTRY: dict[str, type[UniversityCrawlerBase]] = {
    "xjtu-cs": XJTUCSCrawler,
}


def get_crawler_info_list() -> list[dict]:
    """Return metadata for all registered crawlers (for the frontend selector).

    Returns:
        List of dicts with ``university_id`` and ``display_name`` keys.
    """
    return [
        {"university_id": uid, "display_name": cls.display_name}
        for uid, cls in REGISTRY.items()
    ]


def get_crawler(university_id: str) -> UniversityCrawlerBase:
    """Instantiate and return a crawler by its university_id.

    Args:
        university_id: Registered crawler key (e.g. ``"xjtu-cs"``).

    Returns:
        Instantiated crawler ready for use.

    Raises:
        KeyError: If ``university_id`` is not registered.
    """
    cls = REGISTRY[university_id]
    return cls()
