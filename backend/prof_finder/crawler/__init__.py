"""Web crawlers for Prof-Finder."""

from .dblp import DblpClient, extract_dblp_pid_from_url
from .scholar import ScholarCrawler

__all__ = ["ScholarCrawler", "DblpClient", "extract_dblp_pid_from_url"]
