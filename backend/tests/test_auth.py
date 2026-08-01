"""Password hashing and JWT token unit tests."""

from __future__ import annotations

import secrets
from datetime import timedelta

import pytest

from prof_finder.api.auth import (
    _hash_with_salt,
    create_access_token,
    create_refresh_token,
    hash_password,
    needs_rehash,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)


def legacy_hash(password: str) -> str:
    """Build a hash in the pre-bcrypt 'salt$sha256' format."""
    salt = secrets.token_hex(16)
    return f"{salt}${_hash_with_salt(password, salt)}"


class TestPasswordHashing:
    def test_hash_uses_bcrypt(self):
        assert hash_password("secret-pw").startswith("$2b$")

    def test_hash_is_salted(self):
        assert hash_password("secret-pw") != hash_password("secret-pw")

    def test_verify_roundtrip(self):
        hashed = hash_password("secret-pw")
        assert verify_password("secret-pw", hashed)
        assert not verify_password("secret-pw ", hashed)
        assert not verify_password("wrong", hashed)

    def test_long_utf8_password_is_not_truncated(self):
        """bcrypt caps input at 72 bytes; pre-hashing must keep full entropy."""
        base = "密码" * 40  # 240 bytes as UTF-8
        hashed = hash_password(base)
        assert verify_password(base, hashed)
        assert not verify_password(base + "尾", hashed)

    def test_empty_stored_hash_is_rejected(self):
        assert not verify_password("anything", "")

    def test_malformed_hash_is_rejected(self):
        assert not verify_password("anything", "not-a-hash")

    @pytest.mark.parametrize("password", ["short1", "with spaces", "🔐emoji", "a" * 100])
    def test_various_passwords_roundtrip(self, password):
        assert verify_password(password, hash_password(password))


class TestLegacyHashMigration:
    def test_legacy_hash_still_verifies(self):
        hashed = legacy_hash("old-password")
        assert verify_password("old-password", hashed)
        assert not verify_password("other", hashed)

    def test_legacy_hash_is_flagged_for_upgrade(self):
        assert needs_rehash(legacy_hash("old-password"))

    def test_bcrypt_hash_is_not_flagged(self):
        assert not needs_rehash(hash_password("new-password"))

    def test_empty_hash_is_not_flagged(self):
        assert not needs_rehash("")


class TestJwtTokens:
    def test_access_token_roundtrip(self):
        payload = verify_access_token(create_access_token({"sub": "7"}))
        assert payload is not None
        assert payload["sub"] == "7"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        payload = verify_refresh_token(create_refresh_token({"sub": "7"}))
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_access_token_is_not_accepted_as_refresh(self):
        assert verify_refresh_token(create_access_token({"sub": "7"})) is None

    def test_refresh_token_is_not_accepted_as_access(self):
        assert verify_access_token(create_refresh_token({"sub": "7"})) is None

    def test_expired_token_is_rejected(self):
        expired = create_access_token({"sub": "7"}, expires_delta=timedelta(seconds=-10))
        assert verify_access_token(expired) is None

    def test_tampered_token_is_rejected(self):
        token = create_access_token({"sub": "7"})
        assert verify_access_token(token[:-2] + "xy") is None

    def test_garbage_token_is_rejected(self):
        assert verify_access_token("not.a.jwt") is None
