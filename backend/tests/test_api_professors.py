"""Tests for professor management API endpoints."""

import pytest
from fastapi.testclient import TestClient

from prof_finder.models.schema import Professor


class TestProfessorList:
    """Tests for listing professors."""

    def test_list_professors_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test listing professors with pagination."""
        # Create professors
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(
                    user_id=user.id,
                    name=f"Prof {i}",
                    affiliation=f"University {i}",
                    research_interests=["NLP", "ML"],
                )
                for i in range(5)
            ]
            session.add_all(professors)
            session.commit()
        
        response = test_client.get("/api/professors?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_professors_pagination(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test pagination."""
        # Create 10 professors
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(
                    user_id=user.id,
                    name=f"Prof {i}",
                    affiliation=f"University {i}",
                )
                for i in range(10)
            ]
            session.add_all(professors)
            session.commit()
        
        # First page
        response = test_client.get("/api/professors?page=1&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["pages"] == 4  # 10 / 3 = 4 pages
        
        # Second page
        response = test_client.get("/api/professors?page=2&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 2

    def test_list_professors_filter_affiliation(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test filtering by affiliation."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(user_id=user.id, name="Prof A", affiliation="MIT"),
                Professor(user_id=user.id, name="Prof B", affiliation="Stanford"),
            ]
            session.add_all(professors)
            session.commit()
        
        response = test_client.get(
            "/api/professors?affiliation=MIT", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["affiliation"] == "MIT"


class TestProfessorCreate:
    """Tests for creating professors."""

    def test_create_professor_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful professor creation."""
        response = test_client.post(
            "/api/professors",
            headers=auth_headers,
            json={
                "name": "Dr. Smith",
                "affiliation": "Stanford CS",
                "email": "smith@stanford.edu",
                "research_interests": ["NLP", "ML"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dr. Smith"
        assert data["affiliation"] == "Stanford CS"
        assert "NLP" in data["research_interests"]


class TestProfessorGet:
    """Tests for getting a specific professor."""

    def test_get_professor_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test getting a professor."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="Dr. Test",
                affiliation="Test University",
            )
            session.add(professor)
            session.commit()
            professor_id = professor.id
        
        response = test_client.get(f"/api/professors/{professor_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == professor_id
        assert data["name"] == "Dr. Test"

    def test_get_professor_not_found(self, test_client: TestClient, auth_headers: dict):
        """Test getting non-existent professor."""
        response = test_client.get("/api/professors/99999", headers=auth_headers)
        assert response.status_code == 404


class TestProfessorUpdate:
    """Tests for updating professors."""

    def test_update_professor_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful professor update."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="Old Name",
                affiliation="Old University",
            )
            session.add(professor)
            session.commit()
            professor_id = professor.id
        
        response = test_client.put(
            f"/api/professors/{professor_id}",
            headers=auth_headers,
            json={"name": "New Name", "affiliation": "New University"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["affiliation"] == "New University"


class TestProfessorDelete:
    """Tests for deleting professors."""

    def test_delete_professor_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful professor deletion."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="To Delete",
            )
            session.add(professor)
            session.commit()
            professor_id = professor.id
        
        response = test_client.delete(f"/api/professors/{professor_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]
        
        # Verify deleted
        response = test_client.get(f"/api/professors/{professor_id}", headers=auth_headers)
        assert response.status_code == 404


class TestProfessorBatchDelete:
    """Tests for batch deleting professors."""

    def test_batch_delete_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful batch deletion."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(user_id=user.id, name=f"Prof {i}")
                for i in range(3)
            ]
            session.add_all(professors)
            session.commit()
            professor_ids = [p.id for p in professors]
        
        response = test_client.post(
            "/api/professors/batch-delete",
            headers=auth_headers,
            json={"ids": professor_ids[:2]},
        )
        assert response.status_code == 200
        assert "已删除 2 位教授" in response.json()["message"]
