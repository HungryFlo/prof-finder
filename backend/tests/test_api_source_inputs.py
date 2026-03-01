"""Tests for source input API endpoints."""

from pathlib import Path
import tempfile

from fastapi.testclient import TestClient

from prof_finder.models.schema import SourceInput, User


class TestSourceInputPdf:
    """Tests for PDF source input flow."""

    def test_upload_pdf_success(self, test_client: TestClient, auth_headers: dict, monkeypatch):
        """Upload PDF and get extracted markdown."""
        monkeypatch.setattr(
            "prof_finder.api.routes.source_inputs.extract_markdown_from_pdf",
            lambda _path: "# Parsed Markdown",
        )

        response = test_client.post(
            "/api/source-inputs/pdf",
            headers=auth_headers,
            files={"file": ("paper.pdf", b"%PDF-1.4 test", "application/pdf")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "pdf"
        assert data["status"] == "succeeded"
        assert data["metadata_only"] is False
        assert data["extracted_markdown"] == "# Parsed Markdown"

    def test_upload_non_pdf_rejected(self, test_client: TestClient, auth_headers: dict):
        """Reject non-PDF upload."""
        response = test_client.post(
            "/api/source-inputs/pdf",
            headers=auth_headers,
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 400


class TestSourceInputArxiv:
    """Tests for ArXiv source input flow."""

    def test_arxiv_metadata_only_fallback_on_pdf_failure(
        self, test_client: TestClient, auth_headers: dict, monkeypatch
    ):
        """Keep metadata if ArXiv PDF download/parse fails."""
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
        monkeypatch.setattr(
            "prof_finder.api.routes.source_inputs.download_to_temp_file",
            lambda _url: (_ for _ in ()).throw(RuntimeError("download failed")),
        )

        response = test_client.post(
            "/api/source-inputs/arxiv",
            headers=auth_headers,
            json={"url": "https://arxiv.org/abs/1234.56789"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "arxiv"
        assert data["status"] == "failed"
        assert data["metadata_only"] is True
        assert data["title"] == "Test ArXiv Paper"
        assert "稍后重试" in (data["error_message"] or "")

    def test_retry_arxiv_pdf_parse_success(
        self, test_client: TestClient, auth_headers: dict, test_db, monkeypatch
    ):
        """Retry parse should recover metadata-only arXiv source."""
        with test_db.session() as session:
            user = session.query(User).filter(User.username == "testuser").first()
            assert user is not None
            source = SourceInput(
                user_id=user.id,
                source_type="arxiv",
                source_url="https://arxiv.org/abs/1234.56789",
                canonical_id="1234.56789",
                title="Title",
                abstract="Abs",
                pdf_url="https://arxiv.org/pdf/1234.56789.pdf",
                status="failed",
                metadata_only=True,
                error_message="old error",
            )
            session.add(source)
            session.flush()
            source_id = source.id

        def _download(_url: str) -> Path:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(b"%PDF-1.4 fake")
            tmp.flush()
            tmp.close()
            return Path(tmp.name)

        monkeypatch.setattr("prof_finder.api.routes.source_inputs.download_to_temp_file", _download)
        monkeypatch.setattr(
            "prof_finder.api.routes.source_inputs.extract_markdown_from_pdf",
            lambda _path: "# Retried Markdown",
        )

        response = test_client.post(
            f"/api/source-inputs/{source_id}/retry-pdf-parse",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
        assert data["metadata_only"] is False
        assert data["extracted_markdown"] == "# Retried Markdown"
