"""Shared fixtures: an isolated SQLite database and an authenticated API client."""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point the app at a throwaway SQLite file and reset the global handle."""
    from prof_finder.config import settings
    from prof_finder.db import database as database_module
    from prof_finder.utils.query_cache import clear_active_profile_cache

    monkeypatch.setattr(settings, "database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(database_module, "_db", None)
    clear_active_profile_cache()

    db = database_module.get_db()
    yield db

    db.engine.dispose()
    clear_active_profile_cache()


@pytest.fixture
def db_session(temp_db) -> Iterator[Session]:
    session = temp_db.SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client(temp_db) -> TestClient:
    """API client backed by ``temp_db`` with the admin account seeded.

    The lifespan is deliberately not run: it would start the Huey consumer,
    which these tests do not need.
    """
    from prof_finder.api.bootstrap import init_admin_user
    from prof_finder.api.main import create_app

    init_admin_user()
    return TestClient(create_app())


@pytest.fixture
def user_token(client) -> str:
    """Register a regular user and return its access token."""
    client.post("/api/auth/register", json={"username": "tester", "password": "pw-tester-1"})
    response = client.post(
        "/api/auth/login", json={"username": "tester", "password": "pw-tester-1"}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(user_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}
