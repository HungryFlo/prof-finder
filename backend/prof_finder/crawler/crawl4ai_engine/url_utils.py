"""Re-export URL helpers used by crawl4ai (canonical implementation in utils.url_utils)."""

from ...utils.url_utils import resolve_absolute_url

__all__ = ["resolve_absolute_url"]
