"""Active-profile cache behaviour."""

from __future__ import annotations

from prof_finder.models.schema import User, UserProfile
from prof_finder.utils.query_cache import (
    clear_active_profile_cache,
    get_active_profile,
    invalidate_active_profile,
)


def make_user(session, username: str = "cache-user") -> User:
    user = User(username=username, password_hash="x")
    session.add(user)
    session.flush()
    return user


def add_profile(session, user_id: int, title: str, active: bool) -> UserProfile:
    profile = UserProfile(user_id=user_id, title=title, is_active=active)
    session.add(profile)
    session.flush()
    return profile


def test_returns_none_when_no_profile_exists(db_session):
    user = make_user(db_session)
    assert get_active_profile(db_session, user.id) is None


def test_returns_the_active_profile(db_session):
    user = make_user(db_session)
    add_profile(db_session, user.id, "inactive", active=False)
    active = add_profile(db_session, user.id, "active", active=True)

    assert get_active_profile(db_session, user.id).id == active.id


def test_result_is_cached_across_calls(db_session):
    user = make_user(db_session)
    active = add_profile(db_session, user.id, "active", active=True)

    assert get_active_profile(db_session, user.id).id == active.id
    # Flip the flag behind the cache's back; the stale id is still served.
    active.is_active = False
    db_session.flush()
    assert get_active_profile(db_session, user.id).id == active.id


def test_invalidate_forces_a_refetch(db_session):
    user = make_user(db_session)
    first = add_profile(db_session, user.id, "first", active=True)
    get_active_profile(db_session, user.id)

    first.is_active = False
    second = add_profile(db_session, user.id, "second", active=True)
    db_session.flush()

    invalidate_active_profile(user.id)
    assert get_active_profile(db_session, user.id).id == second.id


def test_cache_is_per_user(db_session):
    one = make_user(db_session, "user-one")
    two = make_user(db_session, "user-two")
    profile_one = add_profile(db_session, one.id, "one", active=True)
    profile_two = add_profile(db_session, two.id, "two", active=True)

    assert get_active_profile(db_session, one.id).id == profile_one.id
    assert get_active_profile(db_session, two.id).id == profile_two.id

    invalidate_active_profile(one.id)
    assert get_active_profile(db_session, two.id).id == profile_two.id


def test_clear_wipes_every_entry(db_session):
    user = make_user(db_session)
    profile = add_profile(db_session, user.id, "only", active=True)
    get_active_profile(db_session, user.id)

    profile.is_active = False
    db_session.flush()
    clear_active_profile_cache()

    assert get_active_profile(db_session, user.id) is None
