"""Tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient

from prof_finder.models.schema import User, UserSettings


class TestAuthRegister:
    """Tests for user registration."""

    def test_register_success(self, test_client: TestClient, test_db):
        """Test successful user registration."""
        response = test_client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["is_admin"] is False
        assert data["must_change_password"] is False
        assert "id" in data
        assert "password" not in data  # Password should not be in response

    def test_register_duplicate_username(self, test_client: TestClient, test_user: User):
        """Test registration with duplicate username."""
        response = test_client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_register_reserved_username(self, test_client: TestClient):
        """Test registration with reserved admin username."""
        response = test_client.post(
            "/api/auth/register",
            json={"username": "root", "password": "password123"},
        )
        assert response.status_code == 400
        assert "系统保留" in response.json()["detail"]

    def test_register_short_password(self, test_client: TestClient):
        """Test registration with password too short."""
        response = test_client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "12345"},  # < 6 chars
        )
        assert response.status_code == 422  # Validation error

    def test_register_creates_settings(self, test_client: TestClient, test_db):
        """Test that registration creates default user settings."""
        response = test_client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 201
        
        # Check that settings were created
        with test_db.session() as session:
            user = session.query(User).filter(User.username == "newuser").first()
            assert user is not None
            settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()
            assert settings is not None


class TestAuthLogin:
    """Tests for user login."""

    def test_login_success(self, test_client: TestClient, test_user: User):
        """Test successful login."""
        response = test_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["must_change_password"] is False

    def test_login_wrong_password(self, test_client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = test_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpass"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with non-existent user."""
        response = test_client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_must_change_password(self, test_client: TestClient, test_db):
        """Test login when user must change password."""
        from prof_finder.api.auth import hash_password
        with test_db.session() as session:
            user = User(
                username="mustchange",
                password_hash=hash_password("testpass123"),
                is_admin=False,
                must_change_password=True,
            )
            session.add(user)
            session.commit()
        
        # Login should succeed but indicate password change required
        response = test_client.post(
            "/api/auth/login",
            json={"username": "mustchange", "password": "testpass123"},
        )
        assert response.status_code == 200
        assert response.json()["must_change_password"] is True


class TestAuthRefresh:
    """Tests for token refresh."""

    def test_refresh_success(self, test_client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = test_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different (or same if generated at same time)
        # Just verify we got a valid response
        assert len(data["refresh_token"]) > 0

    def test_refresh_invalid_token(self, test_client: TestClient):
        """Test refresh with invalid token."""
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        assert response.status_code == 401
        assert "无效或已过期" in response.json()["detail"]


class TestAuthMe:
    """Tests for getting current user info."""

    def test_get_me_success(self, test_client: TestClient, auth_headers: dict):
        """Test getting current user info."""
        response = test_client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert "password" not in data

    def test_get_me_unauthorized(self, test_client: TestClient):
        """Test getting user info without authentication."""
        response = test_client.get("/api/auth/me")
        assert response.status_code == 401


class TestAuthChangePassword:
    """Tests for changing password."""

    def test_change_password_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful password change."""
        response = test_client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={"current_password": "testpass123", "new_password": "newpass123"},
        )
        assert response.status_code == 200
        assert "密码修改成功" in response.json()["message"]
        
        # Verify new password works
        login_response = test_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "newpass123"},
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, test_client: TestClient, auth_headers: dict):
        """Test password change with wrong current password."""
        response = test_client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={"current_password": "wrongpass", "new_password": "newpass123"},
        )
        assert response.status_code == 400
        assert "当前密码错误" in response.json()["detail"]

    def test_change_password_clears_must_change_flag(
        self, test_client: TestClient, test_db
    ):
        """Test that password change clears must_change_password flag."""
        # Create user with must_change_password=True
        with test_db.session() as session:
            from prof_finder.api.auth import hash_password
            user = User(
                username="mustchange",
                password_hash=hash_password("oldpass"),
                is_admin=False,
                must_change_password=True,
            )
            session.add(user)
            session.commit()
        
        # Login
        login_response = test_client.post(
            "/api/auth/login",
            json={"username": "mustchange", "password": "oldpass"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Change password
        response = test_client.post(
            "/api/auth/change-password",
            headers=headers,
            json={"current_password": "oldpass", "new_password": "newpass123"},
        )
        assert response.status_code == 200
        
        # Login again should not require password change
        login_response2 = test_client.post(
            "/api/auth/login",
            json={"username": "mustchange", "password": "newpass123"},
        )
        assert login_response2.json()["must_change_password"] is False


class TestAdminAPI:
    """Tests for admin API endpoints."""

    def test_list_users_admin(self, test_client: TestClient, admin_headers: dict, test_user: User):
        """Test admin listing all users."""
        response = test_client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1
        usernames = [u["username"] for u in users]
        assert "testuser" in usernames

    def test_list_users_non_admin(self, test_client: TestClient, auth_headers: dict):
        """Test non-admin cannot list users."""
        response = test_client.get("/api/admin/users", headers=auth_headers)
        assert response.status_code == 403
        assert "权限不足" in response.json()["detail"]

    def test_reset_password_admin(
        self, test_client: TestClient, admin_headers: dict, test_db, test_user
    ):
        """Test admin resetting user password."""
        # Get user ID from active session to avoid detached instance error
        # test_user fixture ensures the user exists
        with test_db.session() as session:
            from prof_finder.models.schema import User
            # Query by username to get fresh instance from active session
            user = session.query(User).filter(User.username == "testuser").first()
            user_id = user.id
        
        response = test_client.post(
            f"/api/admin/users/{user_id}/reset-password",
            headers=admin_headers,
            json={"new_password": "resetpass123"},
        )
        assert response.status_code == 200
        assert "密码已重置" in response.json()["message"]
        
        # Verify new password works
        login_response = test_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "resetpass123"},
        )
        assert login_response.status_code == 200

    def test_reset_password_nonexistent_user(
        self, test_client: TestClient, admin_headers: dict
    ):
        """Test resetting password for non-existent user."""
        response = test_client.post(
            "/api/admin/users/99999/reset-password",
            headers=admin_headers,
            json={"new_password": "newpass123"},
        )
        assert response.status_code == 404
        assert "用户不存在" in response.json()["detail"]
