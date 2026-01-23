"""Google Scholar crawler using scholarly library."""

import time
from typing import Optional
from ..config import settings


class ScholarCrawler:
    """Crawler for Google Scholar data using scholarly library."""

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

    def get_author(self, scholar_id: str) -> Optional[dict]:
        """Get author information by Google Scholar ID.
        
        Args:
            scholar_id: Google Scholar author ID.
            
        Returns:
            Dictionary with author data or None if not found.
        """
        try:
            # Search by scholar ID
            author = self._scholarly.search_author_id(scholar_id)
            
            # Fill in detailed information
            author = self._scholarly.fill(author, sections=["basics", "indices", "publications"])
            
            # Add delay to avoid rate limiting
            time.sleep(settings.request_delay)
            
            return self._parse_author(author, scholar_id)
            
        except Exception as e:
            print(f"Error fetching author {scholar_id}: {e}")
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
            print(f"Error searching for author: {e}")
            
        return results

    def _parse_author(self, author: dict, scholar_id: str) -> dict:
        """Parse scholarly author object into our format.
        
        Args:
            author: Scholarly author object.
            scholar_id: Google Scholar ID.
            
        Returns:
            Parsed author dictionary.
        """
        # Extract publications
        publications = []
        for pub in author.get("publications", [])[:20]:  # Limit to 20 publications
            pub_info = {
                "title": pub.get("bib", {}).get("title", ""),
                "year": pub.get("bib", {}).get("pub_year", ""),
                "citations": pub.get("num_citations", 0),
                "authors": pub.get("bib", {}).get("author", ""),
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
