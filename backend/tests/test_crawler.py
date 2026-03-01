"""Tests for Google Scholar crawler."""

import pytest
from unittest.mock import patch, MagicMock


class TestScholarCrawler:
    """Tests for ScholarCrawler with mocked scholarly library."""

    @pytest.fixture
    def mock_scholarly(self):
        """Create a mock scholarly module."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def crawler(self, mock_scholarly):
        """Create a ScholarCrawler with mocked scholarly."""
        with patch.dict('sys.modules', {'scholarly': mock_scholarly}):
            with patch('prof_finder.crawler.scholar.settings') as mock_settings:
                mock_settings.scholarly_proxy = None
                mock_settings.request_delay = 0  # No delay in tests
                
                from prof_finder.crawler.scholar import ScholarCrawler
                crawler = ScholarCrawler()
                crawler._scholarly = mock_scholarly.scholarly
                return crawler

    def test_get_author_success(self, crawler, mock_scholarly):
        """Test successful author retrieval."""
        # Setup mock responses
        top_cited_author = {
            "name": "Test Author",
            "affiliation": "Test University",
            "email_domain": "test.edu",
            "homepage": "https://test.edu/author",
            "interests": ["Machine Learning", "NLP"],
            "hindex": 50,
            "citedby": 10000,
            "publications": [
                {
                    "bib": {
                        "title": "Test Paper 1",
                        "pub_year": "2023",
                        "author": "Test Author, Co-Author",
                    },
                    "num_citations": 100,
                },
                {
                    "bib": {
                        "title": "Test Paper 2",
                        "pub_year": "2022",
                        "author": "Test Author",
                    },
                    "num_citations": 50,
                },
            ],
        }
        latest_author = {
            "publications": [
                {
                    "bib": {
                        "title": "Test Paper 2",  # Duplicate title should be deduplicated
                        "pub_year": "2024",
                        "author": "Test Author",
                    },
                    "num_citations": 55,
                },
                {
                    "bib": {
                        "title": "Latest Paper",
                        "pub_year": "2025",
                        "author": "Test Author",
                    },
                    "num_citations": 3,
                },
            ]
        }

        crawler._scholarly.search_author_id.side_effect = [top_cited_author, top_cited_author]
        crawler._scholarly.fill.side_effect = [top_cited_author, latest_author]

        # Call method
        result = crawler.get_author("test123")

        # Verify
        assert result is not None
        assert result["name"] == "Test Author"
        assert result["affiliation"] == "Test University"
        assert result["h_index"] == 50
        assert result["citations"] == 10000
        assert len(result["publications"]) == 3
        assert result["publications"][0]["title"] == "Test Paper 1"
        assert result["publications"][-1]["title"] == "Latest Paper"
        assert result["scholar_id"] == "test123"

    def test_get_author_not_found(self, crawler):
        """Test author not found."""
        crawler._scholarly.search_author_id.side_effect = Exception("Not found")
        
        result = crawler.get_author("invalid_id")
        
        assert result is None

    def test_search_author_success(self, crawler):
        """Test successful author search."""
        # Setup mock response as iterator
        mock_results = iter([
            {
                "name": "Author 1",
                "affiliation": "University 1",
                "interests": ["AI"],
                "scholar_id": "id1",
                "citedby": 1000,
            },
            {
                "name": "Author 2",
                "affiliation": "University 2",
                "interests": ["ML"],
                "scholar_id": "id2",
                "citedby": 500,
            },
        ])
        
        crawler._scholarly.search_author.return_value = mock_results
        
        # Call method
        results = crawler.search_author("Test", limit=5)
        
        # Verify
        assert len(results) == 2
        assert results[0]["name"] == "Author 1"
        assert results[1]["name"] == "Author 2"

    def test_search_author_with_limit(self, crawler):
        """Test search respects limit parameter."""
        # Setup mock with more results than limit
        mock_results = iter([
            {"name": f"Author {i}", "affiliation": "", "interests": [], "scholar_id": f"id{i}", "citedby": 0}
            for i in range(10)
        ])
        
        crawler._scholarly.search_author.return_value = mock_results
        
        # Call with limit=3
        results = crawler.search_author("Test", limit=3)
        
        assert len(results) == 3

    def test_search_author_empty_results(self, crawler):
        """Test search with no results."""
        crawler._scholarly.search_author.return_value = iter([])
        
        results = crawler.search_author("NonexistentPerson12345")
        
        assert results == []

    def test_parse_author_with_missing_fields(self, crawler):
        """Test parsing author with missing optional fields."""
        mock_author = {
            "name": "Minimal Author",
            # Missing: affiliation, email_domain, homepage, interests, hindex, citedby
            "publications": [],
        }
        
        result = crawler._parse_author(mock_author, "min123")
        
        assert result["name"] == "Minimal Author"
        assert result["affiliation"] == ""
        assert result["email"] == ""
        assert result["homepage"] == ""
        assert result["interests"] == []
        assert result["h_index"] == 0
        assert result["citations"] == 0
        assert result["publications"] == []

    def test_parse_author_deduplicates_publications(self, crawler):
        """Test deduplication across top-cited and latest lists."""
        mock_author = {
            "name": "Prolific Author",
            "publications": [
                {"bib": {"title": "Paper A", "pub_year": "2023", "author": "Author"}, "num_citations": 100},
                {"bib": {"title": "Paper B", "pub_year": "2022", "author": "Author"}, "num_citations": 90},
            ],
        }
        latest_publications = [
            {"bib": {"title": "Paper B", "pub_year": "2024", "author": "Author"}, "num_citations": 5},
            {"bib": {"title": "Paper C", "pub_year": "2025", "author": "Author"}, "num_citations": 2},
        ]

        result = crawler._parse_author(
            mock_author,
            "prolific123",
            latest_publications=latest_publications,
        )

        assert [pub["title"] for pub in result["publications"]] == ["Paper A", "Paper B", "Paper C"]


class TestScholarCrawlerIntegration:
    """Integration tests that require network (marked for manual run)."""

    @pytest.mark.skip(reason="Requires network access to Google Scholar")
    def test_real_author_fetch(self):
        """Test fetching a real author from Google Scholar."""
        from prof_finder.crawler.scholar import ScholarCrawler
        
        crawler = ScholarCrawler()
        result = crawler.get_author("JicYPdAAAAAJ")  # Geoffrey Hinton
        
        assert result is not None
        assert "Hinton" in result["name"]
        assert result["h_index"] > 100
