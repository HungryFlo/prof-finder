"""Google Scholar crawler using the scholarly library."""

import logging
import time
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


class ScholarCrawler:
    """Crawler for Google Scholar data using scholarly."""

    _PUBLICATION_FETCH_LIMIT = 20

    def __init__(self):
        """Initialize the crawler."""
        try:
            from scholarly import scholarly
            self._scholarly = scholarly
        except ImportError:
            raise ImportError(
                "scholarly library is required. Install with: pip install scholarly"
            )

        if settings.scholarly_proxy:
            from scholarly import ProxyGenerator
            pg = ProxyGenerator()
            pg.SingleProxy(
                http=settings.scholarly_proxy,
                https=settings.scholarly_proxy,
            )
            self._scholarly.use_proxy(pg)

    def get_author(self, scholar_id: str) -> Optional[dict]:
        """Get author information by Google Scholar ID.

        Args:
            scholar_id: Google Scholar author ID.

        Returns:
            Dictionary with author data or None if not found.
        """
        try:
            author = self._scholarly.search_author_id(scholar_id)

            author = self._scholarly.fill(
                author,
                sections=["basics", "indices", "publications"],
                sortby="citedby",
                publication_limit=self._PUBLICATION_FETCH_LIMIT,
            )

            latest_publications: list[dict] = []
            try:
                latest_author = self._scholarly.search_author_id(scholar_id)
                latest_author = self._scholarly.fill(
                    latest_author,
                    sections=["publications"],
                    sortby="year",
                    publication_limit=self._PUBLICATION_FETCH_LIMIT,
                )
                latest_publications = latest_author.get("publications", [])
            except Exception as e:
                logger.warning(
                    "Error fetching latest publications for %s: %s", scholar_id, e
                )

            time.sleep(settings.request_delay)

            return self._parse_author(
                author,
                scholar_id,
                latest_publications=latest_publications,
            )

        except Exception as e:
            logger.warning("scholarly failed for %s: %s", scholar_id, e)
            return None

    def search_author(self, name: str, limit: int = 5) -> list[dict]:
        """Search for authors by name.

        Args:
            name: Author name to search.
            limit: Maximum number of results.

        Returns:
            List of author dictionaries.
        """
        results = []
        try:
            search_query = self._scholarly.search_author(name)

            for i, author in enumerate(search_query):
                if i >= limit:
                    break

                raw_name = author.get("name", "")
                logger.debug(
                    "scholarly result [%d/%d] for '%s': name=%s, aff=%s, id=%s",
                    i + 1, limit, name, raw_name,
                    author.get("affiliation", ""), author.get("scholar_id", ""),
                )
                results.append({
                    "name": raw_name,
                    "affiliation": author.get("affiliation", ""),
                    "interests": author.get("interests", []),
                    "scholar_id": author.get("scholar_id", ""),
                    "citedby": author.get("citedby", 0),
                    "email": author.get("email_domain", ""),
                })

                time.sleep(settings.request_delay)

            if not results:
                logger.warning(
                    "scholarly search returned 0 results for '%s' — "
                    "possible Google blocking or no match",
                    name,
                )

        except Exception as e:
            logger.warning("scholarly search failed for '%s': %s", name, e)

        return results

    def fill_publication(self, author_pub_id: str) -> dict:
        """Fetch detailed publication info by calling scholarly.fill() on one pub.

        Args:
            author_pub_id: The ``author_pub_id`` from a publication snippet.

        Returns:
            Dict with ``abstract``, ``pub_url``, ``eprint_url``, ``journal``,
            ``conference``, ``volume``, ``number``, ``pages``, ``publisher``.
        """
        try:
            from scholarly.data_types import PublicationSource

            pub = {
                "container_type": "Publication",
                "source": PublicationSource.AUTHOR_PUBLICATION_ENTRY,
                "bib": {},
                "filled": False,
                "author_pub_id": author_pub_id,
            }
            filled = self._scholarly.fill(pub)
            bib = filled.get("bib", {})

            return {
                "abstract": bib.get("abstract", ""),
                "pub_url": filled.get("pub_url", ""),
                "eprint_url": filled.get("eprint_url", ""),
                "journal": bib.get("journal", ""),
                "conference": bib.get("conference", ""),
                "volume": bib.get("volume", ""),
                "number": bib.get("number", ""),
                "pages": bib.get("pages", ""),
                "publisher": bib.get("publisher", ""),
            }
        except Exception as e:
            logger.warning(
                "scholarly fill_publication failed for %s: %s", author_pub_id, e
            )
            return {}

    def _parse_author(
        self,
        author: dict,
        scholar_id: str,
        latest_publications: Optional[list[dict]] = None,
    ) -> dict:
        """Parse scholarly author object into our format."""
        publications: list[dict] = []
        seen_titles: set[str] = set()
        publication_sources = [author.get("publications", []), latest_publications or []]
        for source in publication_sources:
            for pub in source:
                title = pub.get("bib", {}).get("title", "")
                normalized_title = " ".join(title.lower().split())
                if normalized_title and normalized_title in seen_titles:
                    continue
                if normalized_title:
                    seen_titles.add(normalized_title)

                author_pub_id = pub.get("author_pub_id", "")
                pub_info = {
                    "title": title,
                    "year": pub.get("bib", {}).get("pub_year", ""),
                    "citations": pub.get("num_citations", 0),
                    "authors": pub.get("bib", {}).get("author", ""),
                    "source": "scholar",
                    "author_pub_id": author_pub_id,
                    "gscholar_url": (
                        f"https://scholar.google.com/citations"
                        f"?view_op=view_citation&hl=en"
                        f"&citation_for_view={author_pub_id}"
                        if author_pub_id else ""
                    ),
                }
                publications.append(pub_info)

        return {
            "name": author.get("name", ""),
            "affiliation": author.get("affiliation", ""),
            "email": author.get("email_domain", ""),
            "homepage": author.get("homepage", ""),
            "interests": author.get("interests", []),
            "h_index": author.get("hindex", 0),
            "citations": author.get("citedby", 0),
            "publications": publications,
            "scholar_id": scholar_id,
        }
