"""Tests for settings API endpoints."""

import pytest
from fastapi.testclient import TestClient

from prof_finder.models.schema import UserSettings


class TestSettingsGet:
    """Tests for getting user settings."""

    def test_get_settings_success(self, test_client: TestClient, auth_headers: dict):
        """Test getting user settings."""
        response = test_client.get("/api/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "llm_api_key_masked" in data
        assert "llm_base_url" in data
        assert "llm_model" in data
        assert "llm_provider" in data
        assert "request_delay" in data
        assert data.get("auto_enrich_on_save_fetch_publication_details") is True
        assert data.get("auto_enrich_on_save_paper_summaries") is True
        assert data.get("auto_enrich_on_save_research_profile") is True

    def test_get_settings_creates_default(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test that getting settings creates default if not exists."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            session.query(UserSettings).filter(UserSettings.user_id == user.id).delete()
            session.commit()

        response = test_client.get("/api/settings", headers=auth_headers)
        assert response.status_code == 200

        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            settings = (
                session.query(UserSettings).filter(UserSettings.user_id == user.id).first()
            )
            assert settings is not None


class TestSettingsUpdate:
    """Tests for updating user settings."""

    def test_update_settings_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful settings update."""
        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "llm_provider": "anthropic",
                "llm_api_key": "new_api_key_12345",
                "llm_base_url": "https://api.example.com/v1",
                "llm_model": "claude-sonnet-4-20250514",
                "request_delay": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["request_delay"] == 5
        assert data["llm_base_url"] == "https://api.example.com/v1"
        assert data["llm_model"] == "claude-sonnet-4-20250514"
        assert data["llm_provider"] == "anthropic"
        assert data["llm_api_key_masked"] is not None
        assert "new_api_key_12345" not in data["llm_api_key_masked"]

    def test_update_settings_partial(self, test_client: TestClient, auth_headers: dict):
        """Test partial settings update."""
        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={"llm_api_key": "partial_update_key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "llm_base_url" in data
        assert "request_delay" in data

    def test_update_settings_creates_if_not_exists(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test that update creates settings if not exists."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            session.query(UserSettings).filter(UserSettings.user_id == user.id).delete()
            session.commit()

        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={"request_delay": 10},
        )
        assert response.status_code == 200

        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            settings = (
                session.query(UserSettings).filter(UserSettings.user_id == user.id).first()
            )
            assert settings is not None
            assert settings.request_delay == 10

    def test_update_auto_enrich_flags(self, test_client: TestClient, auth_headers: dict):
        """Test updating professor auto-enrichment toggles."""
        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "auto_enrich_on_save_fetch_publication_details": False,
                "auto_enrich_on_save_paper_summaries": False,
                "auto_enrich_on_save_research_profile": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["auto_enrich_on_save_fetch_publication_details"] is False
        assert data["auto_enrich_on_save_paper_summaries"] is False
        assert data["auto_enrich_on_save_research_profile"] is True
