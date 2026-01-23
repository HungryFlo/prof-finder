"""Tests for database models."""

import pytest
import tempfile
import os
from datetime import datetime

from prof_finder.db import Database
from prof_finder.models import User, UserProfile, Professor, MatchRecord


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    database = Database(db_path)
    yield database
    
    # Cleanup
    os.unlink(db_path)


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db):
        with db.session() as session:
            user = User(username="testuser")
            session.add(user)
            session.commit()
            
            assert user.id is not None
            assert user.username == "testuser"
            assert user.created_at is not None

    def test_get_or_create_user(self, db):
        # Create new user
        user1 = db.get_or_create_user("newuser")
        assert user1.username == "newuser"
        user1_id = user1.id  # Cache the ID
        
        # Get existing user
        user2 = db.get_or_create_user("newuser")
        assert user2.id == user1_id


class TestUserProfileModel:
    """Tests for UserProfile model."""

    def test_create_profile(self, db):
        with db.session() as session:
            user = User(username="testuser")
            session.add(user)
            session.commit()
            
            profile = UserProfile(
                user_id=user.id,
                title="Test Resume",
                name="Test Name",
                education=[{"degree": "本科", "school": "Test University"}],
                skills=["Python", "NLP"],
                is_active=True,
            )
            session.add(profile)
            session.commit()
            
            assert profile.id is not None
            assert profile.is_active == True
            assert "Python" in profile.skills

    def test_multiple_profiles_per_user(self, db):
        with db.session() as session:
            user = User(username="testuser")
            session.add(user)
            session.commit()
            
            profile1 = UserProfile(user_id=user.id, title="Resume 1", is_active=True)
            profile2 = UserProfile(user_id=user.id, title="Resume 2", is_active=False)
            session.add_all([profile1, profile2])
            session.commit()
            
            profiles = session.query(UserProfile).filter(
                UserProfile.user_id == user.id
            ).all()
            
            assert len(profiles) == 2


class TestProfessorModel:
    """Tests for Professor model."""

    def test_create_professor(self, db):
        with db.session() as session:
            user = User(username="testuser")
            session.add(user)
            session.commit()
            
            professor = Professor(
                user_id=user.id,
                name="Dr. Smith",
                affiliation="Stanford CS",
                research_interests=["NLP", "Machine Learning"],
                google_scholar_id="abc123",
            )
            session.add(professor)
            session.commit()
            
            assert professor.id is not None
            assert professor.name == "Dr. Smith"
            assert "NLP" in professor.research_interests

    def test_user_isolated_professors(self, db):
        with db.session() as session:
            user1 = User(username="user1")
            user2 = User(username="user2")
            session.add_all([user1, user2])
            session.commit()
            
            prof1 = Professor(user_id=user1.id, name="Prof A")
            prof2 = Professor(user_id=user2.id, name="Prof B")
            session.add_all([prof1, prof2])
            session.commit()
            
            # User 1 should only see their professor
            profs = session.query(Professor).filter(
                Professor.user_id == user1.id
            ).all()
            assert len(profs) == 1
            assert profs[0].name == "Prof A"


class TestMatchRecordModel:
    """Tests for MatchRecord model."""

    def test_create_match_record(self, db):
        with db.session() as session:
            user = User(username="testuser")
            session.add(user)
            session.commit()
            
            profile = UserProfile(user_id=user.id, title="Resume")
            professor = Professor(user_id=user.id, name="Dr. Test")
            session.add_all([profile, professor])
            session.commit()
            
            record = MatchRecord(
                user_profile_id=profile.id,
                professor_id=professor.id,
                score=75.5,
                match_reasons=["研究方向匹配: NLP"],
            )
            session.add(record)
            session.commit()
            
            assert record.id is not None
            assert record.score == 75.5
            assert len(record.match_reasons) == 1
