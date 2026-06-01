"""Simple TTL caches for frequently-queried DB objects."""

import time
from typing import Any, Optional, Tuple

# {user_id: (timestamp, UserProfile)}
_active_profile_cache: dict[int, Tuple[float, Any]] = {}
_ACTIVE_PROFILE_TTL = 30  # seconds


def get_active_profile(session: Any, user_id: int) -> Optional[Any]:
    """Return the active UserProfile for *user_id*, using a short-lived cache."""
    from ..models.schema import UserProfile

    cached = _active_profile_cache.get(user_id)
    if cached and (time.time() - cached[0]) < _ACTIVE_PROFILE_TTL:
        return cached[1]

    profile = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == user_id, UserProfile.is_active.is_(True))
        .first()
    )
    _active_profile_cache[user_id] = (time.time(), profile)
    return profile


def invalidate_active_profile(user_id: int) -> None:
    """Clear cached active profile for a user (e.g. after activate/deactivate)."""
    _active_profile_cache.pop(user_id, None)


def clear_active_profile_cache() -> None:
    """Clear the entire active profile cache (for testing)."""
    _active_profile_cache.clear()
