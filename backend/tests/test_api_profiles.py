"""Tests for profile management API endpoints."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO

from prof_finder.models.schema import UserProfile


class TestProfileList:
    """Tests for listing profiles."""

    def test_list_profiles_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test listing user's profiles."""
        # Create a profile
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                name="Test Name",
                skills=["Python", "NLP"],
            )
            session.add(profile)
            session.commit()
        
        response = test_client.get("/api/profiles", headers=auth_headers)
        assert response.status_code == 200
        profiles = response.json()
        assert isinstance(profiles, list)
        assert len(profiles) >= 1
        assert profiles[0]["title"] == "Test Resume"

    def test_list_profiles_empty(self, test_client: TestClient, auth_headers: dict):
        """Test listing profiles when user has none."""
        response = test_client.get("/api/profiles", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_profiles_unauthorized(self, test_client: TestClient):
        """Test listing profiles without authentication."""
        response = test_client.get("/api/profiles")
        assert response.status_code == 401


class TestProfileCreate:
    """Tests for creating profiles."""

    def test_create_profile_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful profile creation."""
        response = test_client.post(
            "/api/profiles",
            headers=auth_headers,
            json={
                "title": "My Resume",
                "name": "John Doe",
                "education": [{"degree": "Bachelor", "school": "MIT"}],
                "research_experience": [],
                "projects": [],
                "skills": ["Python", "ML"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Resume"
        assert data["name"] == "John Doe"
        assert data["is_active"] is True
        assert "Python" in data["skills"]

    def test_create_profile_deactivates_others(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test that creating a profile deactivates other profiles."""
        # Create first profile
        response1 = test_client.post(
            "/api/profiles",
            headers=auth_headers,
            json={"title": "Resume 1", "skills": []},
        )
        profile1_id = response1.json()["id"]
        
        # Create second profile
        response2 = test_client.post(
            "/api/profiles",
            headers=auth_headers,
            json={"title": "Resume 2", "skills": []},
        )
        profile2_id = response2.json()["id"]
        
        # Check that first profile is deactivated
        response = test_client.get(f"/api/profiles/{profile1_id}", headers=auth_headers)
        assert response.json()["is_active"] is False
        
        # Check that second profile is active
        response = test_client.get(f"/api/profiles/{profile2_id}", headers=auth_headers)
        assert response.json()["is_active"] is True


class TestProfileUpload:
    """Tests for uploading and parsing resume files."""

    def test_upload_markdown_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful markdown file upload."""
        content = b"""# John Doe

## Education
- Bachelor: MIT (2018-2022)

## Skills
Python, Machine Learning
"""
        files = {"file": ("resume.md", BytesIO(content), "text/markdown")}
        data = {"title": "My Resume", "use_llm": "false"}
        
        response = test_client.post(
            "/api/profiles/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "parsed_data" in data
        assert data["parsed_data"]["title"] == "My Resume"
        assert "message" in data

    def test_upload_latex_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful LaTeX file upload."""
        content = rb"""
\documentclass{article}
\begin{document}
\name{John Doe}
\section{Skills}
Python, Machine Learning
\end{document}
"""
        files = {"file": ("resume.tex", BytesIO(content), "text/x-latex")}
        data = {"title": "My CV", "use_llm": "false"}
        
        response = test_client.post(
            "/api/profiles/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "parsed_data" in data

    def test_upload_latex_extension_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful .latex file upload."""
        content = rb"""
\documentclass{article}
\begin{document}
\section{Skills}
Python, Machine Learning
\end{document}
"""
        files = {"file": ("resume.latex", BytesIO(content), "text/x-latex")}
        data = {"title": "My CV", "use_llm": "false"}

        response = test_client.post(
            "/api/profiles/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )
        assert response.status_code == 200
        payload = response.json()
        assert "parsed_data" in payload

    def test_upload_invalid_extension(self, test_client: TestClient, auth_headers: dict):
        """Test upload with invalid file extension."""
        files = {"file": ("resume.pdf", BytesIO(b"content"), "application/pdf")}
        data = {"title": "My Resume", "use_llm": "false"}
        
        response = test_client.post(
            "/api/profiles/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )
        assert response.status_code == 400
        assert "仅支持" in response.json()["detail"]

    def test_upload_empty_file(self, test_client: TestClient, auth_headers: dict):
        """Test upload with empty file."""
        files = {"file": ("resume.md", BytesIO(b""), "text/markdown")}
        data = {"title": "My Resume", "use_llm": "false"}
        
        response = test_client.post(
            "/api/profiles/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )
        assert response.status_code == 400
        assert "文件内容为空" in response.json()["detail"]


class TestProfileGet:
    """Tests for getting a specific profile."""

    def test_get_profile_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test getting a profile."""
        # Create profile
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                name="Test Name",
            )
            session.add(profile)
            session.commit()
            profile_id = profile.id
        
        response = test_client.get(f"/api/profiles/{profile_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["title"] == "Test Resume"

    def test_get_profile_not_found(self, test_client: TestClient, auth_headers: dict):
        """Test getting non-existent profile."""
        response = test_client.get("/api/profiles/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "简历不存在" in response.json()["detail"]

    def test_get_profile_other_user(self, test_client: TestClient, test_db, test_user):
        """Test getting another user's profile (should fail)."""
        # Create another user and profile
        with test_db.session() as session:
            from prof_finder.models.schema import User
            from prof_finder.api.auth import hash_password
            other_user = User(
                username="otheruser",
                password_hash=hash_password("pass123"),
            )
            session.add(other_user)
            session.flush()
            profile = UserProfile(
                user_id=other_user.id,
                title="Other Resume",
            )
            session.add(profile)
            session.commit()
            profile_id = profile.id
        
        # Login as testuser (test_user fixture ensures testuser exists)
        login_response = test_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get other user's profile
        response = test_client.get(f"/api/profiles/{profile_id}", headers=headers)
        assert response.status_code == 404


class TestProfileUpdate:
    """Tests for updating profiles."""

    def test_update_profile_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful profile update."""
        # Create profile
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile = UserProfile(
                user_id=user.id,
                title="Old Title",
                name="Old Name",
            )
            session.add(profile)
            session.commit()
            profile_id = profile.id
        
        # Update profile
        response = test_client.put(
            f"/api/profiles/{profile_id}",
            headers=auth_headers,
            json={"title": "New Title", "name": "New Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["name"] == "New Name"

    def test_update_profile_partial(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test partial profile update."""
        # Create profile
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile = UserProfile(
                user_id=user.id,
                title="Original Title",
                name="Original Name",
                skills=["Python"],
            )
            session.add(profile)
            session.commit()
            profile_id = profile.id
        
        # Update only title
        response = test_client.put(
            f"/api/profiles/{profile_id}",
            headers=auth_headers,
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["name"] == "Original Name"  # Unchanged


class TestProfileDelete:
    """Tests for deleting profiles."""

    def test_delete_profile_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful profile deletion."""
        # Create profile
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile = UserProfile(
                user_id=user.id,
                title="To Delete",
            )
            session.add(profile)
            session.commit()
            profile_id = profile.id
        
        # Delete profile
        response = test_client.delete(f"/api/profiles/{profile_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]
        
        # Verify deleted
        response = test_client.get(f"/api/profiles/{profile_id}", headers=auth_headers)
        assert response.status_code == 404


class TestProfileActivate:
    """Tests for activating profiles."""

    def test_activate_profile_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful profile activation."""
        # Create two profiles
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile1 = UserProfile(user_id=user.id, title="Profile 1", is_active=True)
            profile2 = UserProfile(user_id=user.id, title="Profile 2", is_active=False)
            session.add_all([profile1, profile2])
            session.commit()
            profile2_id = profile2.id
        
        # Activate profile2
        response = test_client.post(
            f"/api/profiles/{profile2_id}/activate",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True
        
        # Verify profile1 is deactivated
        profiles = test_client.get("/api/profiles", headers=auth_headers).json()
        profile1_data = next(p for p in profiles if p["title"] == "Profile 1")
        assert profile1_data["is_active"] is False


class TestProfileBatchDelete:
    """Tests for batch deleting profiles."""

    def test_batch_delete_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful batch deletion."""
        # Create multiple profiles
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profiles = [
                UserProfile(user_id=user.id, title=f"Profile {i}")
                for i in range(3)
            ]
            session.add_all(profiles)
            session.commit()
            profile_ids = [p.id for p in profiles]
        
        # Batch delete
        response = test_client.post(
            "/api/profiles/batch-delete",
            headers=auth_headers,
            json={"ids": profile_ids[:2]},
        )
        assert response.status_code == 200
        assert "已删除 2 份简历" in response.json()["message"]
        
        # Verify only one remains
        remaining = test_client.get("/api/profiles", headers=auth_headers).json()
        assert len([p for p in remaining if p["id"] in profile_ids]) == 1
