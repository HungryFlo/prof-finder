"""Dashboard aggregate API."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, defer, load_only

from ...models.schema import MatchRecord, Professor, User, UserProfile
from ...utils.query_cache import get_active_profile
from ..deps import get_current_user, get_db_session
from ..routes.professors import _PROFESSOR_LIST_DEFER, get_professor_list_response
from ..schemas import (
    DashboardResponse,
    ProfileResponse,
    ProfileSummaryResponse,
)

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

_RECENT = 5


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Return dashboard stats and recent slices in one response."""
    profile_count = (
        session.query(func.count(UserProfile.id))
        .filter(UserProfile.user_id == current_user.id)
        .scalar()
        or 0
    )
    professor_count = (
        session.query(func.count(Professor.id))
        .filter(Professor.user_id == current_user.id)
        .scalar()
        or 0
    )

    active_profile = get_active_profile(session, current_user.id)

    recent_profiles = (
        session.query(UserProfile)
        .options(
            load_only(
                UserProfile.id,
                UserProfile.title,
                UserProfile.name,
                UserProfile.is_active,
                UserProfile.source_format,
                UserProfile.experience_pool_id,
                UserProfile.created_at,
                UserProfile.updated_at,
            )
        )
        .filter(UserProfile.user_id == current_user.id)
        .order_by(UserProfile.updated_at.desc())
        .limit(_RECENT)
        .all()
    )

    publication_count = func.coalesce(func.json_array_length(Professor.publications), 0)
    recent_professor_rows = (
        session.query(Professor, publication_count)
        .options(*(defer(col) for col in _PROFESSOR_LIST_DEFER))
        .filter(Professor.user_id == current_user.id)
        .order_by(Professor.created_at.desc())
        .limit(_RECENT)
        .all()
    )

    match_count = 0
    letter_count = 0
    top_matches: list[dict] = []
    recent_letters: list[dict] = []

    if active_profile:
        match_count = (
            session.query(func.count(MatchRecord.id))
            .filter(MatchRecord.user_profile_id == active_profile.id)
            .scalar()
            or 0
        )
        letter_count = (
            session.query(func.count(MatchRecord.id))
            .filter(
                MatchRecord.user_profile_id == active_profile.id,
                MatchRecord.letter_content.isnot(None),
            )
            .scalar()
            or 0
        )

        match_rows = (
            session.query(MatchRecord, Professor)
            .join(Professor, MatchRecord.professor_id == Professor.id)
            .filter(MatchRecord.user_profile_id == active_profile.id)
            .order_by(MatchRecord.score.desc())
            .limit(_RECENT)
            .all()
        )
        top_matches = [
            {
                "professor_id": professor.id,
                "professor_name": professor.name,
                "professor_affiliation": professor.affiliation,
                "score": match_record.score,
                "match_reasons": match_record.match_reasons or [],
                "letter_generated": match_record.letter_content is not None,
            }
            for match_record, professor in match_rows
        ]

        letter_rows = (
            session.query(MatchRecord, Professor)
            .join(Professor, MatchRecord.professor_id == Professor.id)
            .filter(
                MatchRecord.user_profile_id == active_profile.id,
                MatchRecord.letter_content.isnot(None),
            )
            .order_by(MatchRecord.letter_generated_at.desc())
            .limit(_RECENT)
            .all()
        )
        recent_letters = [
            {
                "professor_id": professor.id,
                "professor_name": professor.name,
                "content": match_record.letter_content,
                "generated_at": match_record.letter_generated_at,
                "is_generated": True,
            }
            for match_record, professor in letter_rows
        ]

    return DashboardResponse(
        stats={
            "profile_count": profile_count,
            "professor_count": professor_count,
            "match_count": match_count,
            "letter_count": letter_count,
        },
        active_profile=ProfileResponse.model_validate(active_profile) if active_profile else None,
        recent_profiles=[ProfileSummaryResponse.model_validate(p) for p in recent_profiles],
        recent_professors=[
            get_professor_list_response(p, int(pub_count or 0))
            for p, pub_count in recent_professor_rows
        ],
        top_matches=top_matches,
        recent_letters=recent_letters,
    )
