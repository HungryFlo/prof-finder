"""Authentication endpoint tests."""

from __future__ import annotations

import secrets

from prof_finder.api.auth import _hash_with_salt
from prof_finder.models.schema import User


def test_register_creates_user(client):
    response = client.post(
        "/api/auth/register", json={"username": "alice", "password": "alice-pw-1"}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["username"] == "alice"
    assert body["is_admin"] is False


def test_register_rejects_duplicate_username(client):
    client.post("/api/auth/register", json={"username": "bob", "password": "bob-pw-1"})
    response = client.post(
        "/api/auth/register", json={"username": "bob", "password": "bob-pw-2"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "USERNAME_EXISTS"


def test_register_rejects_reserved_admin_username(client):
    from prof_finder.config import settings

    response = client.post(
        "/api/auth/register",
        json={"username": settings.admin_username, "password": "whatever-1"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "USERNAME_RESERVED"


def test_register_rejects_short_password(client):
    response = client.post("/api/auth/register", json={"username": "carl", "password": "abc"})
    assert response.status_code == 422


def test_login_returns_tokens(client):
    client.post("/api/auth/register", json={"username": "dana", "password": "dana-pw-1"})
    response = client.post(
        "/api/auth/login", json={"username": "dana", "password": "dana-pw-1"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] and body["refresh_token"]


def test_login_rejects_wrong_password(client):
    client.post("/api/auth/register", json={"username": "erin", "password": "erin-pw-1"})
    response = client.post(
        "/api/auth/login", json={"username": "erin", "password": "nope-pw-1"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/api/auth/login", json={"username": "ghost", "password": "ghost-pw-1"}
    )
    assert response.status_code == 401


def test_login_upgrades_legacy_password_hash(client, temp_db):
    """A pre-bcrypt hash must still authenticate and be rewritten as bcrypt."""
    salt = secrets.token_hex(16)
    with temp_db.session() as session:
        session.add(
            User(
                username="legacy",
                password_hash=f"{salt}${_hash_with_salt('legacy-pw-1', salt)}",
                is_admin=False,
                must_change_password=False,
            )
        )

    response = client.post(
        "/api/auth/login", json={"username": "legacy", "password": "legacy-pw-1"}
    )
    assert response.status_code == 200

    with temp_db.session() as session:
        stored = session.query(User).filter(User.username == "legacy").first().password_hash
    assert stored.startswith("$2b$")

    # The rewritten hash must keep accepting the same password.
    again = client.post(
        "/api/auth/login", json={"username": "legacy", "password": "legacy-pw-1"}
    )
    assert again.status_code == 200


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer bogus"})
    assert response.status_code == 401
    assert response.json()["code"] == "TOKEN_INVALID"


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "tester"


def test_refresh_rotates_tokens(client):
    client.post("/api/auth/register", json={"username": "frank", "password": "frank-pw-1"})
    login = client.post(
        "/api/auth/login", json={"username": "frank", "password": "frank-pw-1"}
    ).json()

    response = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_rejects_access_token(client):
    client.post("/api/auth/register", json={"username": "gina", "password": "gina-pw-1"})
    login = client.post(
        "/api/auth/login", json={"username": "gina", "password": "gina-pw-1"}
    ).json()

    response = client.post("/api/auth/refresh", json={"refresh_token": login["access_token"]})
    assert response.status_code == 401


def test_change_password(client, auth_headers):
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "pw-tester-1", "new_password": "pw-tester-2"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    assert (
        client.post(
            "/api/auth/login", json={"username": "tester", "password": "pw-tester-1"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={"username": "tester", "password": "pw-tester-2"}
        ).status_code
        == 200
    )


def test_change_password_rejects_wrong_current(client, auth_headers):
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "not-it-1", "new_password": "pw-tester-3"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "CURRENT_PASSWORD_WRONG"


def test_admin_endpoints_reject_non_admin(client, auth_headers):
    response = client.get("/api/admin/users", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["code"] == "ADMIN_REQUIRED"
