"""Google Scholar crawler using scholarly library (with crawl4ai fallback)."""

import logging
import time
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)


class ScholarCrawler:
    """Crawler for Google Scholar data using scholarly library.

    Falls back to ``Crawl4AIScholarCrawler`` when scholarly fails (e.g. due to
    Google anti-bot blocking).
    """

    _PUBLICATION_FETCH_LIMIT = 20

    def __init__(self):
        """Initialize the crawler."""
        # Import scholarly here to avoid import errors if not installed
        try:
            from scholarly import scholarly
            self._scholarly = scholarly
        except ImportError:
            raise ImportError(
                "scholarly library is required. Install with: pip install scholarly"
            )

        # Configure proxy if set
        if settings.scholarly_proxy:
            self._scholarly.use_proxy(
                http=settings.scholarly_proxy,
                https=settings.scholarly_proxy,
            )

        self._fallback_crawler = None  # lazy init

    def _get_fallback(self):
        """Lazily create the crawl4ai fallback crawler."""
        if self._fallback_crawler is None:
            try:
                from .crawl4ai_engine.scholar_crawler import Crawl4AIScholarCrawler
                self._fallback_crawler = Crawl4AIScholarCrawler()
            except Exception:
                logger.debug("crawl4ai fallback not available")
                self._fallback_crawler = False  # sentinel
        return self._fallback_crawler if self._fallback_crawler else None

    def get_author(self, scholar_id: str) -> Optional[dict]:
        """Get author information by Google Scholar ID.

        Tries scholarly first, falls back to crawl4ai on failure.

        Args:
            scholar_id: Google Scholar author ID.

        Returns:
            Dictionary with author data or None if not found.
        """
        try:
            # Search by scholar ID
            author = self._scholarly.search_author_id(scholar_id)

            # Pull top-cited papers (default order) and core profile fields.
            author = self._scholarly.fill(
                author,
                sections=["basics", "indices", "publications"],
                sortby="citedby",
                publication_limit=self._PUBLICATION_FETCH_LIMIT,
            )

            # Pull latest papers separately and merge with top-cited list.
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
                print(f"Error fetching latest publications for {scholar_id}: {e}")

            # Add delay to avoid rate limiting
            time.sleep(settings.request_delay)

            return self._parse_author(
                author,
                scholar_id,
                latest_publications=latest_publications,
            )

        except Exception as e:
            logger.warning("scholarly failed for %s: %s — trying crawl4ai fallback", scholar_id, e)
            fallback = self._get_fallback()
            if fallback:
                try:
                    result = fallback.get_author(scholar_id)
                    if result:
                        logger.info("crawl4ai fallback succeeded for %s", scholar_id)
                        return result
                except Exception:
                    logger.exception("crawl4ai fallback also failed for %s", scholar_id)
            return None

    def search_author(self, name: str, limit: int = 5) -> list[dict]:
        """Search for authors by name.

        Tries scholarly first, falls back to crawl4ai on failure.

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

                results.append({
                    "name": author.get("name", ""),
                    "affiliation": author.get("affiliation", ""),
                    "interests": author.get("interests", []),
                    "scholar_id": author.get("scholar_id", ""),
                    "citedby": author.get("citedby", 0),
                })

                # Add delay
                time.sleep(settings.request_delay)

        except Exception as e:
            logger.warning("scholarly search failed for '%s': %s — trying crawl4ai fallback", name, e)
            fallback = self._get_fallback()
            if fallback:
                try:
                    results = fallback.search_author(name, limit)
                    if results:
                        logger.info("crawl4ai search fallback succeeded for '%s'", name)
                except Exception:
                    logger.exception("crawl4ai search fallback also failed for '%s'", name)

        return results

    def fill_publication(self, author_pub_id: str) -> dict:
        """Fetch detailed publication info by calling scholarly.fill() on one pub.

        Opens the Google Scholar citation detail page for the given
        *author_pub_id* (1 HTTP request) and returns enriched fields:
        abstract, pub_url, eprint_url, journal, conference, volume, pages, etc.

        Falls back to crawl4ai if scholarly fails.

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
            logger.warning("scholarly fill_publication failed for %s: %s — trying crawl4ai fallback", author_pub_id, e)
            fallback = self._get_fallback()
            if fallback:
                try:
                    result = fallback.fill_publication(author_pub_id)
                    if result:
                        logger.info("crawl4ai fill_publication fallback succeeded for %s", author_pub_id)
                        return result
                except Exception:
                    logger.exception("crawl4ai fill_publication fallback also failed for %s", author_pub_id)
            return {}

    def _parse_author(
        self,
        author: dict,
        scholar_id: str,
        latest_publications: Optional[list[dict]] = None,
    ) -> dict:
        """Parse scholarly author object into our format.
        
        Args:
            author: Scholarly author object.
            scholar_id: Google Scholar ID.
            
        Returns:
            Parsed author dictionary.
        """
        # Merge top-cited and latest publications, de-duplicating by normalized title.
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
            "email": author.get("email_domain", ""),  # Only domain available
            "homepage": author.get("homepage", ""),
            "interests": author.get("interests", []),
            "h_index": author.get("hindex", 0),
            "citations": author.get("citedby", 0),
            "publications": publications,
            "scholar_id": scholar_id,
        }
