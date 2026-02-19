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
        assert "deepseek_api_key_masked" in data
        assert "deepseek_base_url" in data
        assert "request_delay" in data

    def test_get_settings_creates_default(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test that getting settings creates default if not exists."""
        # Delete existing settings
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            session.query(UserSettings).filter(
                UserSettings.user_id == user.id
            ).delete()
            session.commit()
        
        # Get settings (should create default)
        response = test_client.get("/api/settings", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify settings were created
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            settings = session.query(UserSettings).filter(
                UserSettings.user_id == user.id
            ).first()
            assert settings is not None


class TestSettingsUpdate:
    """Tests for updating user settings."""

    def test_update_settings_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful settings update."""
        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "deepseek_api_key": "new_api_key_12345",
                "deepseek_base_url": "https://api.example.com/v1",
                "request_delay": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["request_delay"] == 5
        assert data["deepseek_base_url"] == "https://api.example.com/v1"
        # API key should be masked
        assert data["deepseek_api_key_masked"] is not None
        assert "new_api_key_12345" not in data["deepseek_api_key_masked"]

    def test_update_settings_partial(self, test_client: TestClient, auth_headers: dict):
        """Test partial settings update."""
        # Update only API key
        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={"deepseek_api_key": "partial_update_key"},
        )
        assert response.status_code == 200
        data = response.json()
        # Other fields should remain unchanged
        assert "deepseek_base_url" in data
        assert "request_delay" in data

    def test_update_settings_creates_if_not_exists(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test that update creates settings if not exists."""
        # Delete existing settings
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            session.query(UserSettings).filter(
                UserSettings.user_id == user.id
            ).delete()
            session.commit()
        
        # Update settings (should create)
        response = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={"request_delay": 10},
        )
        assert response.status_code == 200
        
        # Verify settings were created
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            settings = session.query(UserSettings).filter(
                UserSettings.user_id == user.id
            ).first()
            assert settings is not None
            assert settings.request_delay == 10
