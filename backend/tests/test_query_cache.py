"""Tests for active profile query cache."""

from prof_finder.api.auth import hash_password
from prof_finder.models.schema import User, UserProfile
from prof_finder.utils.query_cache import (
    clear_active_profile_cache,
    get_active_profile,
    invalidate_active_profile,
)


def _create_user(session) -> int:
    user = User(
        username="cache_test_user",
        password_hash=hash_password("pass"),
        is_admin=False,
        must_change_password=False,
    )
    session.add(user)
    session.flush()
    return user.id


def test_get_active_profile_returns_session_bound_instance(test_db):
    clear_active_profile_cache()
    with test_db.session() as session:
        user_id = _create_user(session)
        profile = UserProfile(
            user_id=user_id,
            title="",
            name="Active",
            is_active=True,
        )
        session.add(profile)
        session.flush()
        profile_id = profile.id

        first = get_active_profile(session, user_id)
        second = get_active_profile(session, user_id)

        assert first is not None
        assert second is not None
        assert first.id == profile_id
        assert second.id == profile_id


def test_invalidate_active_profile(test_db):
    clear_active_profile_cache()
    with test_db.session() as session:
        user_id = _create_user(session)
        profile = UserProfile(user_id=user_id, title="", name="P", is_active=True)
        session.add(profile)
        session.flush()

        get_active_profile(session, user_id)
        invalidate_active_profile(user_id)
        profile.is_active = False
        session.flush()

        assert get_active_profile(session, user_id) is None
