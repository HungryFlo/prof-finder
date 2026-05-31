"""API datetime serialization uses explicit UTC."""

from datetime import datetime, timezone

from prof_finder.api.schemas import ProfileResponse
from prof_finder.utils.time import as_utc, utc_now


def test_as_utc_treats_naive_as_utc():
    naive = datetime(2024, 5, 20, 12, 0, 0)
    aware = as_utc(naive)
    assert aware.tzinfo == timezone.utc
    assert aware.hour == 12


def test_profile_response_serializes_naive_db_datetime_with_z():
    payload = ProfileResponse.model_validate(
        {
            "id": 1,
            "title": "t",
            "name": "n",
            "name_locales": {},
            "skills": [],
            "education": [],
            "research_experience": [],
            "projects": [],
            "is_active": True,
            "source_format": "manual",
            "profile_generated_at": None,
            "created_at": datetime(2024, 5, 20, 12, 0, 0),
            "updated_at": datetime(2024, 5, 20, 12, 0, 0),
        }
    )
    data = payload.model_dump(mode="json")
    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")


def test_utc_now_is_aware():
    now = utc_now()
    assert now.tzinfo is not None
