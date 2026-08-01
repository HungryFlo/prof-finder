"""Profile endpoint tests, focused on the summary/active listing pair."""

from __future__ import annotations

import pytest


def create_profile(client, headers, title: str) -> dict:
    response = client.post(
        "/api/profiles",
        json={"title": title, "name": "Test Student", "skills": ["python"]},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_summary_is_empty_for_new_user(client, auth_headers):
    body = client.get("/api/profiles/summary", headers=auth_headers).json()
    assert body == {"items": [], "total": 0, "page": 1, "page_size": 20, "pages": 1}


def test_summary_paginates(client, auth_headers):
    for i in range(7):
        create_profile(client, auth_headers, f"profile-{i}")

    first = client.get(
        "/api/profiles/summary", params={"page": 1, "page_size": 3}, headers=auth_headers
    ).json()
    assert first["total"] == 7
    assert first["pages"] == 3
    assert len(first["items"]) == 3

    last = client.get(
        "/api/profiles/summary", params={"page": 3, "page_size": 3}, headers=auth_headers
    ).json()
    assert len(last["items"]) == 1

    ids = {item["id"] for item in first["items"]} | {item["id"] for item in last["items"]}
    assert len(ids) == 4


def test_summary_omits_heavy_fields(client, auth_headers):
    create_profile(client, auth_headers, "lean")
    item = client.get("/api/profiles/summary", headers=auth_headers).json()["items"][0]
    assert set(item) == {
        "id",
        "title",
        "name",
        "is_active",
        "source_format",
        "experience_pool_id",
        "created_at",
        "updated_at",
    }


def test_summary_rejects_oversized_page_size(client, auth_headers):
    response = client.get(
        "/api/profiles/summary", params={"page_size": 1000}, headers=auth_headers
    )
    assert response.status_code == 422


def test_summary_is_scoped_to_the_owner(client, auth_headers):
    create_profile(client, auth_headers, "mine")

    client.post("/api/auth/register", json={"username": "other", "password": "other-pw-1"})
    other = client.post(
        "/api/auth/login", json={"username": "other", "password": "other-pw-1"}
    ).json()["access_token"]

    body = client.get(
        "/api/profiles/summary", headers={"Authorization": f"Bearer {other}"}
    ).json()
    assert body["total"] == 0


def test_active_endpoint_returns_null_without_profiles(client, auth_headers):
    assert client.get("/api/profiles/active", headers=auth_headers).json() is None


def test_newest_profile_becomes_active(client, auth_headers):
    create_profile(client, auth_headers, "first")
    second = create_profile(client, auth_headers, "second")

    active = client.get("/api/profiles/active", headers=auth_headers).json()
    assert active["id"] == second["id"]


def test_activate_switches_the_active_profile(client, auth_headers):
    """Also guards the active-profile cache, which must be invalidated here."""
    first = create_profile(client, auth_headers, "first")
    create_profile(client, auth_headers, "second")

    # Populate the cache before switching.
    client.get("/api/profiles/active", headers=auth_headers)

    client.post(f"/api/profiles/{first['id']}/activate", headers=auth_headers)
    active = client.get("/api/profiles/active", headers=auth_headers).json()
    assert active["id"] == first["id"]


def test_delete_clears_the_cached_active_profile(client, auth_headers):
    profile = create_profile(client, auth_headers, "only")
    assert client.get("/api/profiles/active", headers=auth_headers).json()["id"] == profile["id"]

    client.delete(f"/api/profiles/{profile['id']}", headers=auth_headers)
    assert client.get("/api/profiles/active", headers=auth_headers).json() is None


def test_batch_delete_clears_the_cached_active_profile(client, auth_headers):
    first = create_profile(client, auth_headers, "first")
    second = create_profile(client, auth_headers, "second")
    client.get("/api/profiles/active", headers=auth_headers)

    client.post(
        "/api/profiles/batch-delete",
        json={"ids": [first["id"], second["id"]]},
        headers=auth_headers,
    )
    assert client.get("/api/profiles/active", headers=auth_headers).json() is None


@pytest.mark.parametrize("path", ["/api/profiles/summary", "/api/profiles/active"])
def test_endpoints_require_auth(client, path):
    assert client.get(path).status_code == 401
