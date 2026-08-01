"""Profile management API routes."""

import asyncio
import logging
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from ...models.schema import User, UserProfile
from ...models.schema import ExperiencePool
from ...utils.query_cache import get_active_profile, invalidate_active_profile
from ..deps import get_db_session, get_current_user, get_current_user_sse
from ..schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileChatRequest,
    ProfileChatResponse,
    ProfileChatRefineRequest,
    ProfileSummaryListResponse,
    ProfileSummaryResponse,
    TaskStartResponse,
    BatchDeleteRequest,
    MessageResponse,
)
logger = logging.getLogger(__name__)

from ..task_manager import (
    MAX_PROFILE_MATERIAL_CHARS,
    cleanup_old_tasks,
    create_task,
    enqueue_task,
)
from ...llm.config import llm_not_configured_message, llm_provider_for_user_settings
from ...llm.student_profile_generator import StudentProfileGenerator
from ...models.schema import UserSettings
from ..errors import ErrorCode, raise_api_error
from ..experience_pool_service import format_pool_stories_material

router = APIRouter(prefix="/profiles", tags=["学生画像"])


def _validate_experience_pool_id(
    session: Session, user_id: int, pool_id: Optional[int]
) -> Optional[int]:
    if pool_id is None:
        return None
    pool = (
        session.query(ExperiencePool)
        .filter(ExperiencePool.id == pool_id, ExperiencePool.user_id == user_id)
        .first()
    )
    if not pool:
        raise_api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.EXPERIENCE_POOL_NOT_FOUND,
            "信息池不存在",
        )
    return pool_id


def _student_profile_generator(
    session: Session,
    user_id: int,
) -> StudentProfileGenerator:
    user_settings = (
        session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    )
    provider = llm_provider_for_user_settings(user_settings)
    if not provider.enabled:
        raise_api_error(status.HTTP_503_SERVICE_UNAVAILABLE, ErrorCode.LLM_NOT_CONFIGURED, llm_not_configured_message())
    return StudentProfileGenerator(provider=provider)

SUPPORTED_PROFILE_MATERIAL_EXTENSIONS = {".md", ".markdown", ".txt", ".tex", ".latex"}


@router.get("", response_model=List[ProfileResponse])
def list_profiles(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List all profiles for current user.

    Args:
        current_user: Authenticated user.
        session: Database session.

    Returns:
        List of user's profiles.
    """
    profiles = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id)
        .order_by(UserProfile.updated_at.desc())
        .all()
    )
    return profiles


# Declared before "/{profile_id}" so the literal paths win the route match.
@router.get("/summary", response_model=ProfileSummaryListResponse)
def list_profile_summaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List profiles without their generated-content fields.

    Feeds list and picker UIs, which only need identifying columns rather than
    every profile's full analysis payload.
    """
    from sqlalchemy.orm import load_only

    query = session.query(UserProfile).filter(UserProfile.user_id == current_user.id)
    total = query.count()
    items = (
        query.options(
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
        .order_by(UserProfile.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ProfileSummaryListResponse(
        items=[ProfileSummaryResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/active", response_model=Optional[ProfileResponse])
def get_active_profile_route(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Return the active profile, or null when none is active."""
    return get_active_profile(session, current_user.id)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create a new profile manually.

    Args:
        data: Profile data.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Created profile.
    """
    # Deactivate other profiles
    session.query(UserProfile).filter(
        UserProfile.user_id == current_user.id,
        UserProfile.is_active == True,
    ).update({"is_active": False})

    pool_id = _validate_experience_pool_id(
        session, current_user.id, data.experience_pool_id
    )

    # Create new profile
    profile = UserProfile(
        user_id=current_user.id,
        title=data.title,
        name=data.name,
        name_locales=data.name_locales or {},
        education=[e.model_dump() for e in data.education],
        research_experience=[r.model_dump() for r in data.research_experience],
        projects=[p.model_dump() for p in data.projects],
        skills=data.skills,
        raw_content=data.raw_content,
        source_format=data.source_format,
        experience_pool_id=pool_id,
        is_active=True,
    )
    session.add(profile)
    session.flush()
    session.refresh(profile)
    invalidate_active_profile(current_user.id)

    return profile


@router.post("/upload", response_model=TaskStartResponse)
async def upload_profile(
    file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File(default=[]),
    title: str = Form(...),
    use_llm: bool = Form(True),
    research_interests: str = Form(""),
    personal_statement: str = Form(""),
    research_plan: str = Form(""),
    notes: str = Form(""),
    experience_pool_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Upload profile materials and start a background generation/save task.

    Args:
        file: Legacy single resume/material file.
        files: Multiple profile material files.
        title: Profile title.
        use_llm: Whether to use LLM for legacy resume field extraction.
        research_interests: Directly entered research interests.
        personal_statement: Directly entered personal statement.
        research_plan: Directly entered research plan.
        notes: Directly entered free-form notes.
        experience_pool_id: Optional bound experience pool.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for progress tracking via SSE.
    """
    uploaded_files: List[UploadFile] = []
    if file and file.filename:
        uploaded_files.append(file)
    uploaded_files.extend(item for item in files if item.filename)

    manual_inputs = {
        "research_interests": research_interests.strip(),
        "personal_statement": personal_statement.strip(),
        "research_plan": research_plan.strip(),
        "notes": notes.strip(),
    }
    pool_id = _validate_experience_pool_id(
        session, current_user.id, experience_pool_id
    )
    pool_material = None
    if pool_id is not None:
        pool_material = format_pool_stories_material(session, pool_id, language="zh")

    has_manual_input = any(manual_inputs.values())
    if not uploaded_files and not has_manual_input and pool_material is None:
        raise_api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.PROFILE_MATERIAL_REQUIRED,
            "请至少上传一个材料文件、填写一项画像材料，或绑定含细化经历的信息池",
        )

    materials = []
    for upload in uploaded_files:
        filename = upload.filename or ""
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_PROFILE_MATERIAL_EXTENSIONS:
            raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFILE_FILE_TYPE_UNSUPPORTED, "仅支持 .md/.markdown/.txt/.tex/.latex 格式的文件")

        content = await upload.read()
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFILE_FILE_ENCODING_ERROR, f"文件编码错误，请使用 UTF-8 编码：{filename}")

        if not text_content.strip():
            raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFILE_FILE_EMPTY, f"文件内容为空：{filename}")

        materials.append(
            {
                "source_type": "file",
                "filename": filename,
                "extension": ext,
                "content": text_content,
            }
        )

    if pool_material is not None:
        materials.append(pool_material)

    total_chars = sum(len(item["content"]) for item in materials) + sum(
        len(value) for value in manual_inputs.values()
    )
    if total_chars > MAX_PROFILE_MATERIAL_CHARS:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFILE_MATERIAL_TOO_LONG, f"画像材料过长，请控制在 {MAX_PROFILE_MATERIAL_CHARS} 字符以内")

    cleanup_old_tasks()
    task = create_task(
        task_type="profile-generate",
        task_name=f"生成学生画像 · {title}",
        user_id=current_user.id,
        total=3,
    )
    enqueue_task(
        "profile-generate",
        task.task_id,
        title=title,
        materials=materials,
        manual_inputs=manual_inputs,
        use_llm=use_llm,
        experience_pool_id=pool_id,
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message="已启动学生画像生成任务，完成后会自动保存到列表",
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get a specific profile.

    Args:
        profile_id: Profile ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Profile details.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update a profile.

    Args:
        profile_id: Profile ID.
        data: Update data.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Updated profile.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    # Update fields
    if data.title is not None:
        profile.title = data.title
    if data.name is not None:
        profile.name = data.name
    if data.name_locales is not None:
        profile.name_locales = data.name_locales
    if data.education is not None:
        profile.education = [e.model_dump() for e in data.education]
    if data.research_experience is not None:
        profile.research_experience = [r.model_dump() for r in data.research_experience]
    if data.projects is not None:
        profile.projects = [p.model_dump() for p in data.projects]
    if data.skills is not None:
        profile.skills = data.skills
    if "experience_pool_id" in data.model_fields_set:
        profile.experience_pool_id = _validate_experience_pool_id(
            session, current_user.id, data.experience_pool_id
        )

    session.flush()
    session.refresh(profile)

    return profile


@router.delete("/{profile_id}", response_model=MessageResponse)
def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Delete a profile.

    Args:
        profile_id: Profile ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Success message.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    session.delete(profile)
    invalidate_active_profile(current_user.id)

    return MessageResponse(message="画像已删除")


@router.post("/{profile_id}/activate", response_model=ProfileResponse)
def activate_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Activate a profile (deactivate others).

    Args:
        profile_id: Profile ID to activate.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Activated profile.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    # Deactivate all profiles
    session.query(UserProfile).filter(
        UserProfile.user_id == current_user.id,
    ).update({"is_active": False})

    # Activate selected profile
    profile.is_active = True
    session.flush()
    session.refresh(profile)
    invalidate_active_profile(current_user.id)

    return profile


@router.post("/batch-delete", response_model=MessageResponse)
def batch_delete_profiles(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Batch delete profiles.

    Args:
        data: List of profile IDs to delete.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Success message with count.
    """
    deleted_count = (
        session.query(UserProfile)
        .filter(UserProfile.id.in_(data.ids), UserProfile.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    invalidate_active_profile(current_user.id)

    return MessageResponse(message=f"已删除 {deleted_count} 份画像")


@router.post("/{profile_id}/chat", response_model=ProfileChatResponse)
def profile_chat(
    profile_id: int,
    data: ProfileChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """AI interviewer chat: send a message and get the next AI question.

    Args:
        profile_id: Profile ID.
        data: User message + full chat history.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        AI interviewer reply.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    generator = _student_profile_generator(session, current_user.id)

    analysis = profile.profile_analysis or {}
    academic_profile = profile.academic_profile or ""

    try:
        reply = generator.interview(
            profile_analysis=analysis,
            academic_profile=academic_profile,
            history=data.history,
            message=data.message,
            locale=data.locale,
        )
    except ValueError as exc:
        raise_api_error(status.HTTP_503_SERVICE_UNAVAILABLE, ErrorCode.PROFILE_OPERATION_FAILED, str(exc))

    return ProfileChatResponse(reply=reply)


@router.post("/{profile_id}/chat/stream")
async def profile_chat_stream(
    profile_id: int,
    data: ProfileChatRequest,
    current_user: User = Depends(get_current_user_sse),
    session: Session = Depends(get_db_session),
):
    """Streaming AI interviewer response via SSE.

    Yields ``token`` events for each content chunk, ``done`` on completion,
    and ``error`` on failure.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    generator = _student_profile_generator(session, current_user.id)

    analysis = profile.profile_analysis or {}
    academic_profile = profile.academic_profile or ""

    async def event_generator():
        q: queue.Queue[tuple[str, str]] = queue.Queue()
        stop = threading.Event()

        def producer():
            try:
                for token in generator.interview_stream(
                    profile_analysis=analysis,
                    academic_profile=academic_profile,
                    history=data.history,
                    message=data.message,
                    locale=data.locale,
                ):
                    if stop.is_set():
                        return
                    q.put(("token", token))
                q.put(("done", ""))
            except ValueError as exc:
                q.put(("error", str(exc)))
            except Exception:
                logger.exception("Chat stream failed for profile %s", profile_id)
                q.put(("error", "Internal server error"))

        t = threading.Thread(target=producer, daemon=True)
        t.start()

        try:
            while True:
                try:
                    evt, payload = q.get(timeout=0.05)
                    yield {"event": evt, "data": payload}
                    if evt in ("done", "error"):
                        break
                except queue.Empty:
                    await asyncio.sleep(0.05)
        finally:
            stop.set()
            t.join(timeout=10)

    return EventSourceResponse(event_generator())


@router.post("/{profile_id}/chat/refine", response_model=TaskStartResponse)
def profile_chat_refine(
    profile_id: int,
    data: ProfileChatRefineRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to regenerate the profile from chat Q&A.

    Args:
        profile_id: Profile ID.
        data: Full chat history.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for progress tracking via SSE.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    _student_profile_generator(session, current_user.id)

    if not data.history:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFILE_CHAT_REQUIRED, "请先与 AI 进行至少一轮对话")

    cleanup_old_tasks()
    task = create_task(
        task_type="profile-refine",
        task_name=f"优化学生画像 · {profile.title}",
        user_id=current_user.id,
        total=4,
    )
    task.total = 4
    enqueue_task(
        "profile-refine",
        task.task_id,
        profile_id=profile_id,
        chat_history=data.history,
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message="画像优化任务已启动，完成后自动更新",
    )
