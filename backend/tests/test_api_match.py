"""Tests for match API endpoints."""

import pytest
from fastapi.testclient import TestClient

from prof_finder.models.schema import UserProfile, Professor, MatchRecord


class TestMatchRun:
    """Tests for running matching."""

    def test_run_match_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test that POST /match/run starts an async task and returns task_id."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()

            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                name="Test Name",
                skills=["NLP", "Machine Learning"],
                research_experience=[{"title": "NLP Research", "organization": "Lab"}],
                is_active=True,
            )
            session.add(profile)
            session.flush()

            professors = [
                Professor(
                    user_id=user.id,
                    name=f"Prof {i}",
                    affiliation=f"University {i}",
                    research_interests=["NLP", "ML"] if i < 2 else ["CV"],
                )
                for i in range(3)
            ]
            session.add_all(professors)
            session.commit()

        response = test_client.post("/api/match/run", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Route is async: returns task_id immediately, not a completed result.
        assert "task_id" in data
        assert "匹配任务已启动" in data["message"]

    def test_run_match_no_active_profile(self, test_client: TestClient, auth_headers: dict):
        """Test match run without active profile."""
        response = test_client.post("/api/match/run", headers=auth_headers)
        assert response.status_code == 400
        assert "请先激活一份简历" in response.json()["detail"]

    def test_run_match_no_professors(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test match run without professors."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                is_active=True,
            )
            session.add(profile)
            session.commit()
        
        response = test_client.post("/api/match/run", headers=auth_headers)
        assert response.status_code == 400
        assert "请先添加教授" in response.json()["detail"]


class TestMatchResults:
    """Tests for getting match results."""

    def test_get_match_results_success(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test getting match results."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            
            # Create active profile
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                is_active=True,
            )
            session.add(profile)
            session.flush()
            
            # Create professor and match record
            professor = Professor(
                user_id=user.id,
                name="Dr. Test",
                affiliation="Test University",
            )
            session.add(professor)
            session.flush()
            
            match_record = MatchRecord(
                user_profile_id=profile.id,
                professor_id=professor.id,
                score=85.5,
                match_reasons=["研究方向匹配"],
            )
            session.add(match_record)
            session.commit()
        
        response = test_client.get("/api/match/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["score"] == 85.5

    def test_get_match_results_pagination(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test paginated match results."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                is_active=True,
            )
            session.add(profile)
            session.flush()
            
            # Create multiple professors and match records
            for i in range(5):
                professor = Professor(
                    user_id=user.id,
                    name=f"Prof {i}",
                )
                session.add(professor)
                session.flush()
                
                match_record = MatchRecord(
                    user_profile_id=profile.id,
                    professor_id=professor.id,
                    score=80.0 - i,
                )
                session.add(match_record)
            session.commit()
        
        response = test_client.get("/api/match/results?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["score"] > data["items"][1]["score"]  # Sorted by score desc

    def test_get_match_results_min_score_filter(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test filtering by minimum score."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                is_active=True,
            )
            session.add(profile)
            session.flush()
            
            # Create match records with different scores
            for score in [90, 70, 50]:
                professor = Professor(user_id=user.id, name=f"Prof {score}")
                session.add(professor)
                session.flush()
                
                match_record = MatchRecord(
                    user_profile_id=profile.id,
                    professor_id=professor.id,
                    score=score,
                )
                session.add(match_record)
            session.commit()
        
        response = test_client.get("/api/match/results?min_score=75", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["score"] == 90


class TestMatchDetail:
    """Tests for getting match detail."""

    def test_get_match_detail_success(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test getting match detail."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                is_active=True,
            )
            session.add(profile)
            session.flush()
            
            professor = Professor(
                user_id=user.id,
                name="Dr. Test",
                affiliation="Test University",
                research_interests=["NLP"],
            )
            session.add(professor)
            session.flush()
            
            match_record = MatchRecord(
                user_profile_id=profile.id,
                professor_id=professor.id,
                score=85.5,
                match_reasons=["研究方向匹配: NLP"],
            )
            session.add(match_record)
            session.commit()
            professor_id = professor.id
        
        response = test_client.get(
            f"/api/match/results/{professor_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["professor_id"] == professor_id
        assert data["score"] == 85.5
        assert len(data["match_reasons"]) == 1

    def test_get_match_detail_not_found(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test getting match detail for non-existent match."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                is_active=True,
            )
            session.add(profile)
            session.commit()
        
        response = test_client.get("/api/match/results/99999", headers=auth_headers)
        assert response.status_code == 404
