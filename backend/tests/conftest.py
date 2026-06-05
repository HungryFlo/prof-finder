"""Pytest configuration and shared fixtures for API tests."""

import pytest
import tempfile
import os
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import httpx

from prof_finder.db.database import Database, get_db
from prof_finder.models.schema import Base, User, UserSettings
from prof_finder.api.main import create_app
from prof_finder.api.auth import hash_password
from prof_finder.api import deps
from prof_finder.utils.query_cache import clear_active_profile_cache


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear module-level caches between tests."""
    clear_active_profile_cache()
    yield


@pytest.fixture(scope="function")
def test_db() -> Generator[Database, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    database = Database(db_path)
    yield database
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture(scope="function")
def test_client(test_db: Database) -> Generator[TestClient, None, None]:
    """Create a test client with a temporary database."""
    # Override get_db_session dependency
    def override_get_db_session():
        session = test_db.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    app = create_app()
    app.dependency_overrides[deps.get_db_session] = override_get_db_session
    
    # Workaround for httpx 0.28 compatibility issue with starlette TestClient
    # httpx 0.28 changed Client.__init__ signature, starlette 0.36.3 doesn't support it
    # Use httpx directly with ASGITransport (async) wrapped in sync calls
    from starlette.testclient import TestClient as StarletteTestClient
    import inspect
    
    # Check if TestClient can be instantiated
    try:
        # Try to create TestClient normally
        client = StarletteTestClient(app)
    except TypeError as e:
        if "unexpected keyword argument 'app'" in str(e):
            # httpx 0.28 compatibility: monkey-patch or use alternative
            # For now, let's use a workaround by patching httpx.Client
            import httpx._client
            original_init = httpx.Client.__init__
            
            def patched_init(self, *args, **kwargs):
                # Remove 'app' from kwargs if present (it's handled by transport)
                kwargs.pop('app', None)
                return original_init(self, *args, **kwargs)
            
            httpx.Client.__init__ = patched_init
            try:
                client = StarletteTestClient(app)
            finally:
                # Restore original
                httpx.Client.__init__ = original_init
        else:
            raise
    
    yield client
    
    if hasattr(client, 'close'):
        client.close()
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Database) -> User:
    """Create a test user."""
    with test_db.session() as session:
        user = User(
            username="testuser",
            password_hash=hash_password("testpass123"),
            is_admin=False,
            must_change_password=False,
        )
        session.add(user)
        session.flush()
        
        # Create default settings
        settings = UserSettings(
            user_id=user.id,
            llm_provider="openai",
            llm_api_key="test_key",
            llm_base_url="https://api.deepseek.com/v1",
            llm_model="deepseek-chat",
            request_delay=3,
        )
        session.add(settings)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def admin_user(test_db: Database) -> User:
    """Create an admin user."""
    with test_db.session() as session:
        user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            is_admin=True,
            must_change_password=False,
        )
        session.add(user)
        session.flush()
        
        # Create default settings
        settings = UserSettings(
            user_id=user.id,
            llm_provider="openai",
            llm_api_key="admin_key",
            llm_base_url="https://api.deepseek.com/v1",
            llm_model="deepseek-chat",
            request_delay=3,
        )
        session.add(settings)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def auth_headers(test_client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = test_client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(test_client: TestClient, admin_user: User) -> dict:
    """Get authentication headers for admin user."""
    response = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
