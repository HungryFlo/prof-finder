"""Dashboard aggregate endpoint tests."""


def test_dashboard_empty_for_new_user(client, auth_headers):
    body = client.get("/api/dashboard", headers=auth_headers).json()
    assert body["stats"] == {
        "profile_count": 0,
        "professor_count": 0,
        "match_count": 0,
        "letter_count": 0,
    }
    assert body["active_profile"] is None
    assert body["recent_profiles"] == []
    assert body["recent_professors"] == []
    assert body["top_matches"] == []
    assert body["recent_letters"] == []


def test_dashboard_requires_auth(client):
    assert client.get("/api/dashboard").status_code == 401


def test_stream_ticket_requires_auth(client):
    assert client.post("/api/tasks/stream-ticket").status_code == 401


def test_stream_ticket_returns_token(client, auth_headers):
    body = client.post("/api/tasks/stream-ticket", headers=auth_headers).json()
    assert isinstance(body.get("token"), str)
    assert body["token"]
