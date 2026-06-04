"""Tests for source input API endpoints."""

from fastapi.testclient import TestClient


class TestSourceInputArxiv:
    """Tests for ArXiv source input flow."""

    def test_create_arxiv_success(self, test_client: TestClient, auth_headers: dict, monkeypatch):
        """Create ArXiv source from metadata API."""
        monkeypatch.setattr(
            "prof_finder.api.routes.source_inputs.normalize_arxiv_id",
            lambda _url: "1234.56789",
        )
        monkeypatch.setattr(
            "prof_finder.api.routes.source_inputs.fetch_arxiv_metadata",
            lambda _id: {
                "title": "Test ArXiv Paper",
                "abstract": "An abstract.",
                "pdf_url": "https://arxiv.org/pdf/1234.56789.pdf",
            },
        )

        response = test_client.post(
            "/api/source-inputs/arxiv",
            headers=auth_headers,
            json={"url": "https://arxiv.org/abs/1234.56789"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "arxiv"
        assert data["status"] == "succeeded"
        assert data["metadata_only"] is False
        assert data["title"] == "Test ArXiv Paper"
        assert data["abstract"] == "An abstract."

    def test_create_arxiv_invalid_url(self, test_client: TestClient, auth_headers: dict):
        """Reject invalid ArXiv URL."""
        response = test_client.post(
            "/api/source-inputs/arxiv",
            headers=auth_headers,
            json={"url": "https://example.com/not-arxiv"},
        )
        assert response.status_code == 400
