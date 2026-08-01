"""Background task state management and execution coroutines.

Task execution is backed by Huey (SqliteHuey).  Tasks are enqueued via
``enqueue_task()`` and executed by the Huey consumer thread.  Task state
is stored both in-memory (for fast SSE reads) and in the ``background_tasks``
DB table (for persistence across restarts).
"""

import logging
import threading
import time
import re
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from ..utils.query_cache import invalidate_active_profile
from ..utils.time import as_utc, utc_now
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from typing import Callable, Dict, Iterator, List, Optional, Any
from urllib.parse import urlparse, parse_qs


def _llm_provider_for_user_settings_row(user_settings) -> "LLMProvider":
    from ..ai_workflows.provider import LLMProvider
    from ..llm.config import llm_provider_for_user_settings

    return llm_provider_for_user_settings(user_settings)


class TaskStatus(str, Enum):
    """Task lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    # Process was killed/crashed while this task was running and it had not
    # been cancelled by the user.  Distinct from CANCELLED (explicit user
    # intent) and FAILED (an exception during execution).  Surfaced to the
    # user on next startup so they can explicitly choose to resume or discard
    # it, rather than silently re-running (which would duplicate work) or
    # silently disappearing.
    INTERRUPTED = "interrupted"


class TaskCancelled(Exception):
    """Raised inside a task executor when cancellation is requested."""


@dataclass
class TaskState:
    """State of a background task."""

    task_id: str
    task_type: str  # batch-crawl | batch-letters | single-crawl | match | single-letter | paper-summary | profile-parse | profile-generate | professor-profile | professor-enrichment | batch-professor-enrichment | batch-dblp-match | generic-university-crawl | fill-publications | professor-homepage-crawl | batch-refresh | profile-refine
    task_name: str
    user_id: int
    status: TaskStatus
    total: int
    current: int = 0
    success_count: int = 0
    failed_count: int = 0
    message: str = ""
    error_message: str = ""
    results: List[Dict[str, Any]] = field(default_factory=list)
    cancel_requested: bool = False
    created_at: datetime = field(default_factory=utc_now)
    # Huey result ID for revocation of not-yet-started tasks
    huey_result_id: Optional[str] = None
    # Original enqueue arguments for rehydration on restart
    enqueue_args: list = field(default_factory=list)
    enqueue_kwargs: dict = field(default_factory=dict)
    # If this task was spawned by another task (e.g. batch-crawl spawning a
    # batch-professor-enrichment follow-up), cancelling/resolving the parent
    # cascades to the child.
    parent_task_id: Optional[str] = None


# In-memory task registry (primary for SSE reads; backed by background_tasks DB table)
_tasks: Dict[str, TaskState] = {}
_tasks_lock = threading.Lock()

MAX_PROFILE_MATERIAL_CHARS = 60000


@contextmanager
def _session_scope(session_factory: Callable[[], Any]) -> Iterator[Any]:
    """Create a short-lived SQLAlchemy session from a factory."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Task registry helpers
# ---------------------------------------------------------------------------


def create_task(
    task_type: str,
    task_name: str,
    user_id: int,
    total: int,
    *,
    parent_task_id: Optional[str] = None,
) -> TaskState:
    """Create and register a new task (in-memory + DB)."""
    task_id = str(uuid.uuid4())
    task = TaskState(
        task_id=task_id,
        task_type=task_type,
        task_name=task_name,
        user_id=user_id,
        status=TaskStatus.PENDING,
        total=total,
        parent_task_id=parent_task_id,
    )
    with _tasks_lock:
        _tasks[task_id] = task
    persist_task(task)
    return task


def get_child_tasks(parent_task_id: str) -> List[TaskState]:
    """Return all known tasks spawned by the given parent task."""
    with _tasks_lock:
        return [t for t in _tasks.values() if t.parent_task_id == parent_task_id]


def _finalize(task: TaskState, success_status: Optional["TaskStatus"] = None) -> None:
    """Set the terminal status of a task, giving cancellation priority.

    This is the single place where a task's success-path final status is
    decided.  It MUST be used instead of writing ``task.status = ...``
    directly at the end of an executor, because a cancel request may have
    arrived after the last cooperative cancel-check but before the executor
    finished its current step — without this re-check here, that cancel
    request would silently be overwritten by ``COMPLETED``.
    """
    success_status = success_status or TaskStatus.COMPLETED
    task.status = TaskStatus.CANCELLED if task.cancel_requested else success_status
    persist_task(task)


def get_task(task_id: str) -> Optional[TaskState]:
    """Look up a task by ID (thread-safe)."""
    with _tasks_lock:
        return _tasks.get(task_id)


def get_user_tasks(user_id: int) -> List[TaskState]:
    """Return PENDING / RUNNING / FAILED / INTERRUPTED tasks for a user (for UI recovery)."""
    with _tasks_lock:
        return [
            t
            for t in _tasks.values()
            if t.user_id == user_id
            and t.status
            in (
                TaskStatus.PENDING,
                TaskStatus.RUNNING,
                TaskStatus.FAILED,
                TaskStatus.INTERRUPTED,
            )
        ]


def persist_task(task: TaskState) -> None:
    """Write the current task state to the BackgroundTask DB row."""
    from ..models.background_task import BackgroundTask
    from ..db.database import get_db

    try:
        db = get_db()
        with db.session() as session:
            row = (
                session.query(BackgroundTask)
                .filter(BackgroundTask.task_id == task.task_id)
                .first()
            )
            if row:
                row.status = task.status.value
                row.current = task.current
                row.total = task.total
                row.success_count = task.success_count
                row.failed_count = task.failed_count
                row.message = task.message
                row.error_message = task.error_message
                row.results = task.results
                row.cancel_requested = task.cancel_requested
                row.enqueue_args = task.enqueue_args
                row.enqueue_kwargs = task.enqueue_kwargs
                row.parent_task_id = task.parent_task_id
                row.updated_at = datetime.now(timezone.utc)
            else:
                session.add(
                    BackgroundTask(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        task_name=task.task_name,
                        user_id=task.user_id,
                        status=task.status.value,
                        total=task.total,
                        current=task.current,
                        success_count=task.success_count,
                        failed_count=task.failed_count,
                        message=task.message,
                        error_message=task.error_message,
                        results=task.results,
                        cancel_requested=task.cancel_requested,
                        enqueue_args=task.enqueue_args,
                        enqueue_kwargs=task.enqueue_kwargs,
                        parent_task_id=task.parent_task_id,
                    )
                )
    except Exception:
        # Losing this write means progress and crash-recovery state silently drift
        # from reality, so it is reported rather than debug-logged.
        logger.warning("Failed to persist task %s state", task.task_id, exc_info=True)


_last_cleanup_ts: float = 0.0


def cleanup_old_tasks() -> None:
    """Remove completed / cancelled tasks older than 5 minutes from memory."""
    global _last_cleanup_ts
    now_ts = time.time()
    if now_ts - _last_cleanup_ts < 60:
        return
    _last_cleanup_ts = now_ts
    now = utc_now()
    with _tasks_lock:
        stale = [
            tid
            for tid, t in _tasks.items()
            if t.status
            in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED)
            and (now - as_utc(t.created_at)).total_seconds() > 300
        ]
        for tid in stale:
            del _tasks[tid]


# ---------------------------------------------------------------------------
# URL utility (shared by executor and professor route)
# ---------------------------------------------------------------------------


def extract_dblp_pid_from_url(url: str) -> str:
    """Extract DBLP pid from profile URL (delegates to crawler.dblp)."""
    from ..crawler.dblp import extract_dblp_pid_from_url as _extract

    return _extract(url)


def extract_scholar_id_from_url(url: str) -> str:
    """Extract Google Scholar author ID from a profile URL.

    Args:
        url: Google Scholar profile URL.

    Returns:
        Scholar ID string.

    Raises:
        ValueError: If the URL format is unrecognised.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "user" in params:
        return params["user"][0]

    match = re.search(r"user=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)

    raise ValueError("无法从 URL 中提取 Scholar ID，请确保 URL 格式正确")


def _profile_material_metadata(materials: list[dict], manual_inputs: dict) -> list[dict]:
    """Return material metadata, preserving content for refinement use."""
    metadata: list[dict] = []
    for item in materials:
        entry: dict = {
            "source_type": item.get("source_type", "file"),
            "filename": item.get("filename"),
            "extension": item.get("extension"),
        }
        content = item.get("content") or ""
        if content:
            entry["content"] = content
        metadata.append(entry)
    for field_name, value in manual_inputs.items():
        if str(value or "").strip():
            metadata.append(
                {
                    "source_type": "manual",
                    "field": field_name,
                    "char_count": len(str(value)),
                }
            )
    return metadata


def _format_profile_raw_content(materials: list[dict], manual_inputs: dict) -> str:
    """Format all source material into one raw content field."""
    blocks: list[str] = []
    if manual_inputs:
        manual_lines = [
            f"{key}: {value}"
            for key, value in manual_inputs.items()
            if str(value or "").strip()
        ]
        if manual_lines:
            blocks.append("## 手填信息\n" + "\n\n".join(manual_lines))
    for idx, item in enumerate(materials, start=1):
        label = item.get("filename") or f"material-{idx}"
        blocks.append(f"## 上传材料：{label}\n{item.get('content') or ''}")
    return "\n\n".join(blocks)


def _parse_materials_as_resume(materials: list[dict], use_llm: bool) -> dict:
    """Extract legacy resume fields from uploaded materials when possible."""
    from ..parser.smart_parser import SmartParser

    parser = SmartParser(prefer_llm=use_llm)
    merged = {
        "name": None,
        "education": [],
        "research_experience": [],
        "projects": [],
        "skills": [],
    }
    seen_skills: set[str] = set()
    for item in materials:
        content = item.get("content") or ""
        if not content.strip():
            continue
        parsed, _ = parser.parse(content, item.get("extension") or ".md")
        if not merged["name"] and parsed.name:
            merged["name"] = parsed.name
        for edu in parsed.education:
            entry = edu.to_dict()
            if entry not in merged["education"]:
                merged["education"].append(entry)
        for exp in parsed.research_experience:
            entry = exp.to_dict()
            if entry not in merged["research_experience"]:
                merged["research_experience"].append(entry)
        for proj in parsed.projects:
            entry = proj.to_dict()
            if entry not in merged["projects"]:
                merged["projects"].append(entry)
        for skill in parsed.skills:
            normalized = skill.strip()
            if normalized and normalized.lower() not in seen_skills:
                seen_skills.add(normalized.lower())
                merged["skills"].append(normalized)
    return merged


# ---------------------------------------------------------------------------
# Background execution functions (sync — called by Huey consumer thread)
# ---------------------------------------------------------------------------

from .task_queue import register_task, enqueue_task  # noqa: E402
from .enrichment_prefs import (  # noqa: E402
    AutoEnrichFlags,
    any_auto_enrich_substep_enabled,
    flags_from_user_settings_row,
    planned_enrichment_step_count_for_professor,
)


@register_task("batch-crawl")
def execute_batch_crawl(task_id: str, scholar_urls: List[str]) -> None:
    """Crawl a list of Google Scholar URLs and persist each author."""
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.scholar import ScholarCrawler

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    persist_task(task)
    db = get_db()
    crawler = ScholarCrawler()
    new_professor_ids: List[int] = []

    for i, url in enumerate(scholar_urls):
        if i < task.current:
            continue  # already processed before an interruption; resuming
        if task.cancel_requested:
            break

        task.current = i + 1
        task.message = f"正在爬取第 {i + 1}/{task.total} 个..."

        try:
            scholar_id = extract_scholar_id_from_url(url)
            author_data = crawler.get_author(scholar_id)

            if author_data:
                with db.session() as session:
                    existing = (
                        session.query(Professor)
                        .filter(
                            Professor.user_id == task.user_id,
                            Professor.google_scholar_id == author_data["scholar_id"],
                        )
                        .first()
                    )
                    if not existing:
                        professor = Professor(
                            user_id=task.user_id,
                            name=author_data["name"],
                            affiliation=author_data.get("affiliation"),
                            email=author_data.get("email"),
                            homepage=author_data.get("homepage"),
                            google_scholar_id=author_data["scholar_id"],
                            google_scholar_url=url,
                            research_interests=author_data.get("interests", []),
                            publications=author_data.get("publications", []),
                            h_index=author_data.get("h_index"),
                            total_citations=author_data.get("citations"),
                        )
                        from ..utils.name_locales import (
                            apply_inferred_locales_from_name,
                            merge_name_locales,
                        )

                        apply_inferred_locales_from_name(professor)
                        merge_name_locales(professor, en=author_data.get("name"))
                        session.add(professor)
                        session.flush()
                        new_professor_ids.append(professor.id)

                task.success_count += 1
                task.results.append({"url": url, "name": author_data["name"], "success": True})
            else:
                task.failed_count += 1
                task.results.append({"url": url, "success": False, "error": "未找到学者信息"})

        except Exception as e:
            task.failed_count += 1
            task.results.append({"url": url, "success": False, "error": str(e)})

        # Checkpoint each URL so an interrupted run resumes where it stopped.
        persist_task(task)

    _finalize(task)

    if new_professor_ids and task.status == TaskStatus.COMPLETED:
        with db.session() as session:
            row = (
                session.query(UserSettings)
                .filter(UserSettings.user_id == task.user_id)
                .first()
            )
            enrich_flags = flags_from_user_settings_row(row)
        if any_auto_enrich_substep_enabled(enrich_flags):
            batch_enrich = create_task(
                "batch-professor-enrichment",
                f"教授信息增强 ({len(new_professor_ids)} 位)",
                task.user_id,
                total=len(new_professor_ids),
                parent_task_id=task.task_id,
            )
            enqueue_task(
                "batch-professor-enrichment",
                batch_enrich.task_id,
                professor_ids=new_professor_ids,
            )


@register_task("batch-letters")
def execute_batch_letters(
    task_id: str,
    professor_ids: List[int],
    profile_id: int,
    user_id: int,
    language: str,
) -> None:
    """Generate contact letters for a list of professors."""
    from ..db.database import get_db
    from ..models.schema import MatchRecord, Professor, UserProfile, UserSettings
    from ..ai_workflows.workflows import generate_letter

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    persist_task(task)
    db = get_db()
    with db.session() as session:
        user_settings = (
            session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        )
        provider = _llm_provider_for_user_settings_row(user_settings)

    for i, professor_id in enumerate(professor_ids):
        if i < task.current:
            continue  # already processed before an interruption; resuming
        if task.cancel_requested:
            break

        task.current = i + 1

        try:
            with db.session() as session:
                result = (
                    session.query(MatchRecord, Professor, UserProfile)
                    .join(Professor, MatchRecord.professor_id == Professor.id)
                    .join(UserProfile, MatchRecord.user_profile_id == UserProfile.id)
                    .filter(
                        MatchRecord.user_profile_id == profile_id,
                        MatchRecord.professor_id == professor_id,
                    )
                    .first()
                )

                if not result:
                    task.failed_count += 1
                    task.results.append(
                        {"professor_id": professor_id, "success": False, "error": "未找到匹配记录"}
                    )
                    continue

                match_record, professor, profile = result
                task.message = f"正在为 {professor.name} 生成邮件..."
                prof_name = professor.name

                from .experience_pool_service import format_pool_stories_summary

                experience_stories = ""
                if profile.experience_pool_id:
                    experience_stories = format_pool_stories_summary(
                        session,
                        profile.experience_pool_id,
                        language=language if language in ("zh", "en") else "en",
                    )

                profile_data = {
                    "name": profile.name,
                    "name_locales": profile.name_locales or {},
                    "education": profile.education or [],
                    "research_experience": profile.research_experience or [],
                    "projects": profile.projects or [],
                    "skills": profile.skills or [],
                    "academic_profile": profile.academic_profile,
                    "profile_analysis": profile.profile_analysis or {},
                    "experience_stories": experience_stories,
                }
                prof_data = {
                    "name": professor.name,
                    "name_locales": professor.name_locales or {},
                    "affiliation": professor.affiliation,
                    "research_interests": professor.research_interests or [],
                    "publications": professor.publications or [],
                    "research_profile": professor.research_profile,
                    "research_profile_analysis": professor.research_profile_analysis or {},
                }
                reasons = match_record.match_reasons or []

            letter_content = generate_letter(
                student_info=profile_data,
                professor_info=prof_data,
                match_reasons=reasons,
                language=language,
                provider=provider,
                cancel_checker=lambda: task.cancel_requested,
            )

            with db.session() as session:
                mr = (
                    session.query(MatchRecord)
                    .filter(
                        MatchRecord.user_profile_id == profile_id,
                        MatchRecord.professor_id == professor_id,
                    )
                    .first()
                )
                if mr:
                    mr.letter_content = letter_content
                    mr.letter_generated_at = datetime.now(timezone.utc)

            task.success_count += 1
            task.results.append(
                {"professor_id": professor_id, "professor_name": prof_name, "success": True}
            )

        except Exception as e:
            from ..ai_workflows.provider import LLMCancelled

            if isinstance(e, LLMCancelled):
                break
            task.failed_count += 1
            task.results.append({"professor_id": professor_id, "success": False, "error": str(e)})

    _finalize(task)


@register_task("profile-parse")
def execute_profile_parse(
    task_id: str,
    *,
    title: str,
    text_content: str,
    extension: str,
    use_llm: bool,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Parse an uploaded resume and persist it as a user profile."""
    from ..db.database import get_db
    from ..models.schema import UserProfile
    from ..llm.config import llm_provider_for_user_settings
    from ..models.schema import UserSettings
    from ..parser.smart_parser import SmartParser

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.current = 0
    task.total = 1
    task.message = "正在解析画像..."
    source_format = "markdown" if extension in [".md", ".markdown"] else "latex"

    try:
        if session_factory is None:
            db = get_db()
            with db.session() as session:
                user_settings = (
                    session.query(UserSettings)
                    .filter(UserSettings.user_id == task.user_id)
                    .first()
                )
                llm_provider = llm_provider_for_user_settings(user_settings)
        else:
            with _session_scope(session_factory) as session:
                user_settings = (
                    session.query(UserSettings)
                    .filter(UserSettings.user_id == task.user_id)
                    .first()
                )
                llm_provider = llm_provider_for_user_settings(user_settings)

        parser = SmartParser(prefer_llm=use_llm, llm_provider=llm_provider)
        parsed, parse_method = parser.parse(text_content, extension)

        if task.cancel_requested:
            raise TaskCancelled()

        task.message = "正在保存画像..."
        if session_factory is None:
            session_context = get_db().session
        else:

            def session_context():
                return _session_scope(session_factory)

        with session_context() as session:
            has_active_profile = (
                session.query(UserProfile)
                .filter(UserProfile.user_id == task.user_id, UserProfile.is_active == True)
                .first()
                is not None
            )
            profile = UserProfile(
                user_id=task.user_id,
                title=title,
                name=parsed.name,
                education=[
                    {
                        "degree": e.degree,
                        "school": e.school,
                        "major": e.major,
                        "period": e.period,
                    }
                    for e in parsed.education
                ],
                research_experience=[
                    {
                        "title": r.title,
                        "organization": r.organization,
                        "description": r.description,
                        "period": r.period,
                    }
                    for r in parsed.research_experience
                ],
                projects=[{"name": p.name, "description": p.description} for p in parsed.projects],
                skills=parsed.skills,
                raw_content=text_content,
                source_format=source_format,
                is_active=not has_active_profile,
            )
            session.add(profile)
            session.flush()
            profile_id = profile.id
            profile_title = profile.title
            is_active = profile.is_active

        if is_active:
            invalidate_active_profile(task.user_id)

        task.success_count = 1
        task.current = 1
        task.message = f"画像解析完成：{profile_title}"
        task.results.append(
            {
                "success": True,
                "profile_id": profile_id,
                "title": profile_title,
                "parse_method": parse_method,
                "is_active": is_active,
            }
        )
        task.status = TaskStatus.COMPLETED
        persist_task(task)

    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        task.message = "画像解析已取消"
        persist_task(task)
    except Exception as e:
        task.failed_count = 1
        task.status = TaskStatus.FAILED
        task.error_message = f"解析失败: {str(e)}"
        task.message = "画像解析失败"
        persist_task(task)


@register_task("profile-generate")
def execute_student_profile_generation(
    task_id: str,
    *,
    title: str,
    materials: list[dict],
    manual_inputs: dict,
    use_llm: bool,
    experience_pool_id: Optional[int] = None,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Generate an academic student profile from uploaded and manual materials."""
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..ai_workflows.provider import LLMProvider
    from ..ai_workflows.workflows import generate_student_profile
    from ..models.schema import UserProfile, UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.current = 0
    task.total = 3
    task.message = "正在准备画像材料..."

    try:
        material_chars = sum(len(item.get("content") or "") for item in materials)
        manual_chars = sum(len(str(value or "")) for value in manual_inputs.values())
        if material_chars + manual_chars > MAX_PROFILE_MATERIAL_CHARS:
            raise ValueError(
                f"画像材料过长，请控制在 {MAX_PROFILE_MATERIAL_CHARS} 字符以内后重试"
            )

        task.message = "正在提取背景结构化信息..."
        parsed_resume = _parse_materials_as_resume(materials, use_llm)
        task.current = 1
        persist_task(task)

        if task.cancel_requested:
            raise TaskCancelled()

        if session_factory is None:
            session_context = get_db().session
        else:

            def session_context():
                return _session_scope(session_factory)

        with session_context() as session:
            user_settings = (
                session.query(UserSettings).filter(UserSettings.user_id == task.user_id).first()
            )
            provider = _llm_provider_for_user_settings_row(user_settings)
        task.message = "正在生成学生学术画像..."
        result = generate_student_profile(
            materials=materials,
            manual_inputs=manual_inputs,
            language="en",
            provider=provider,
        )
        task.current = 2
        task.message = "正在保存学生画像..."
        persist_task(task)

        if task.cancel_requested:
            raise TaskCancelled()

        with session_context() as session:
            has_active_profile = (
                session.query(UserProfile)
                .filter(UserProfile.user_id == task.user_id, UserProfile.is_active == True)
                .first()
                is not None
            )
            profile = UserProfile(
                user_id=task.user_id,
                title=title,
                name=parsed_resume["name"],
                education=parsed_resume["education"],
                research_experience=parsed_resume["research_experience"],
                projects=parsed_resume["projects"],
                skills=parsed_resume["skills"],
                raw_content=_format_profile_raw_content(materials, manual_inputs),
                source_format="materials",
                profile_materials=_profile_material_metadata(materials, manual_inputs),
                manual_inputs=manual_inputs,
                academic_profile=result.academic_profile,
                profile_analysis=result.profile_analysis,
                evidence_notes=result.evidence_notes,
                conflict_notes=result.conflict_notes,
                profile_generated_at=datetime.now(timezone.utc),
                experience_pool_id=experience_pool_id,
                is_active=not has_active_profile,
            )
            session.add(profile)
            session.flush()
            profile_id = profile.id
            profile_title = profile.title
            is_active = profile.is_active

        if is_active:
            invalidate_active_profile(task.user_id)

        task.success_count = 1
        task.current = 3
        task.message = f"学生画像生成完成：{profile_title}"
        persist_task(task)
        task.results.append(
            {
                "success": True,
                "profile_id": profile_id,
                "title": profile_title,
                "is_active": is_active,
            }
        )
        task.status = TaskStatus.COMPLETED
        persist_task(task)

    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        task.message = "学生画像生成已取消"
        persist_task(task)
    except Exception as e:
        task.failed_count = 1
        task.status = TaskStatus.FAILED
        task.error_message = f"画像生成失败: {str(e)}"
        task.message = "学生画像生成失败"
        persist_task(task)


@register_task("single-crawl")
def execute_single_crawl(task_id: str, scholar_url: str) -> None:
    """Crawl a single Google Scholar profile and persist the professor."""
    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在爬取教授信息..."
    persist_task(task)

    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.scholar import ScholarCrawler

    db = get_db()

    try:
        scholar_id = extract_scholar_id_from_url(scholar_url)
        crawler = ScholarCrawler()
        author_data = crawler.get_author(scholar_id)

        if not author_data:
            task.status = TaskStatus.FAILED
            task.error_message = "未找到该学者信息"
            persist_task(task)
            return

        if task.cancel_requested:
            task.status = TaskStatus.CANCELLED
            persist_task(task)
            return

        with db.session() as session:
            existing = (
                session.query(Professor)
                .filter(
                    Professor.user_id == task.user_id,
                    Professor.google_scholar_id == author_data["scholar_id"],
                )
                .first()
            )
            from ..utils.name_locales import (
                apply_inferred_locales_from_name,
                apply_scholar_name_update,
                merge_name_locales,
            )

            if existing:
                # Professor already linked — update Scholar data in place
                professor = existing
                from ..utils.profile_merge import apply_external_affiliation

                apply_external_affiliation(professor, author_data.get("affiliation"))
                professor.email = author_data.get("email") or professor.email
                professor.homepage = author_data.get("homepage") or professor.homepage
                professor.google_scholar_url = scholar_url
                professor.research_interests = author_data.get("interests") or professor.research_interests
                from ..utils.publication_merge import merge_publications

                professor.publications = merge_publications(
                    professor.publications,
                    author_data.get("publications") or [],
                    "scholar",
                )
                professor.h_index = author_data.get("h_index") or professor.h_index
                professor.total_citations = author_data.get("citations") or professor.total_citations
                apply_scholar_name_update(professor, author_data.get("name"))
            else:
                professor = Professor(
                    user_id=task.user_id,
                    name=author_data["name"],
                    affiliation=author_data.get("affiliation"),
                    email=author_data.get("email"),
                    homepage=author_data.get("homepage"),
                    google_scholar_id=author_data["scholar_id"],
                    google_scholar_url=scholar_url,
                    research_interests=author_data.get("interests", []),
                    publications=author_data.get("publications", []),
                    h_index=author_data.get("h_index"),
                    total_citations=author_data.get("citations"),
                    source="google_scholar",
                )
                apply_inferred_locales_from_name(professor)
                merge_name_locales(professor, en=author_data.get("name"))
                session.add(professor)

            session.flush()
            enrichment_professor_id = professor.id
            settings_row = (
                session.query(UserSettings)
                .filter(UserSettings.user_id == task.user_id)
                .first()
            )
            enrich_flags = flags_from_user_settings_row(settings_row)
            enrich_planned = planned_enrichment_step_count_for_professor(
                professor, enrich_flags
            )

        task.success_count = 1
        task.current = 1
        task.message = f"教授爬取完成：{author_data['name']}"
        task.results.append({"name": author_data["name"], "success": True})
        task.status = TaskStatus.COMPLETED
        persist_task(task)

        if enrich_planned > 0:
            enrich_task = create_task(
                "professor-enrichment",
                "教授信息增强",
                task.user_id,
                total=enrich_planned,
                parent_task_id=task.task_id,
            )
            enqueue_task(
                "professor-enrichment",
                enrich_task.task_id,
                professor_id=enrichment_professor_id,
            )

    except ValueError as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        persist_task(task)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"爬取失败: {str(e)}"
        persist_task(task)


_MATCH_WRITE_BATCH = 25


def _encode_match_inputs(
    professor_texts: list[str],
    profile_text: str,
) -> tuple[list[list[float]], list[float]]:
    """Load the model and encode match inputs.

    Uses asymmetric encoding: professors are encoded as documents, profile as a query.
    Returns (professor_embeddings, profile_embedding).
    """
    from ..matcher.semantic_matcher import encode_texts, encode_query_texts

    prof_vecs = []
    if professor_texts:
        vecs = encode_texts(professor_texts)
        prof_vecs = [v.tolist() for v in vecs]
    profile_vec = encode_query_texts([profile_text])[0].tolist()
    return prof_vecs, profile_vec


def _persist_match_records(
    db, profile_id: int, entries: list[tuple[int, float, list[str]]]
) -> None:
    """Upsert a batch of match records in one short transaction."""
    from ..models.schema import MatchRecord

    if not entries:
        return
    professor_ids = [professor_id for professor_id, _, _ in entries]
    with db.session() as session:
        existing = {
            record.professor_id: record
            for record in session.query(MatchRecord)
            .filter(
                MatchRecord.user_profile_id == profile_id,
                MatchRecord.professor_id.in_(professor_ids),
            )
            .all()
        }
        for professor_id, score, reasons in entries:
            record = existing.get(professor_id)
            if record:
                record.score = score
                record.match_reasons = reasons
            else:
                session.add(
                    MatchRecord(
                        user_profile_id=profile_id,
                        professor_id=professor_id,
                        score=score,
                        match_reasons=reasons,
                    )
                )


@register_task("match")
def execute_match(task_id: str, profile_id: int) -> None:
    """Run semantic matching against all professors using Qwen3-Embedding-0.6B embeddings.

    Model loading and encoding run synchronously in the consumer thread.
    """
    from ..db.database import get_db
    from ..models.schema import UserProfile, Professor
    from ..matcher.semantic_matcher import (
        SemanticMatcher,
        build_professor_text,
        build_profile_text,
    )

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在加载语义匹配模型..."
    persist_task(task)
    db = get_db()

    try:
        # Read everything the match needs, then release the transaction: model
        # loading and encoding take minutes and must not hold the SQLite write lock.
        with db.session() as session:
            active_profile = session.query(UserProfile).filter(UserProfile.id == profile_id).first()
            if not active_profile:
                task.status = TaskStatus.FAILED
                task.error_message = "画像不存在"
                persist_task(task)
                return

            professors = session.query(Professor).filter(Professor.user_id == task.user_id).all()
            if not professors:
                task.status = TaskStatus.FAILED
                task.error_message = "请先添加教授"
                persist_task(task)
                return

            profile_data = {
                "name": active_profile.name,
                "education": active_profile.education or [],
                "research_experience": active_profile.research_experience or [],
                "projects": active_profile.projects or [],
                "skills": active_profile.skills or [],
                "academic_profile": active_profile.academic_profile,
                "profile_analysis": active_profile.profile_analysis or {},
            }

            professor_rows = [
                {
                    "id": p.id,
                    "name": p.name,
                    "affiliation": p.affiliation or "",
                    "research_interests": p.research_interests or [],
                    "publications": p.publications or [],
                    "paper_summaries": p.paper_summaries or [],
                    "research_profile": p.research_profile,
                    "research_profile_analysis": p.research_profile_analysis or {},
                    # Discard stale vectors from an older model (e.g. SPECTER).
                    "embedding": p.embedding if p.embedding and len(p.embedding) == 1024 else None,
                }
                for p in professors
            ]

        match_reason_lang = "en"
        profile_text = build_profile_text(profile_data)
        missing = [row for row in professor_rows if row["embedding"] is None]
        professor_texts = [build_professor_text(row) for row in missing]

        task.message = "正在计算语义向量（首次需从 ModelScope 下载模型）..."
        persist_task(task)
        prof_vecs, profile_vec = _encode_match_inputs(professor_texts, profile_text)

        if missing:
            for row, vec in zip(missing, prof_vecs):
                row["embedding"] = vec
            with db.session() as session:
                for row in missing:
                    session.query(Professor).filter(Professor.id == row["id"]).update(
                        {"embedding": row["embedding"]}, synchronize_session=False
                    )

        matcher = SemanticMatcher()
        task.message = "正在语义匹配..."

        pending: list[tuple[int, float, list[str]]] = []
        for i, row in enumerate(professor_rows):
            if i < task.current:
                continue
            if task.cancel_requested:
                break

            task.current = i + 1
            task.message = f"正在匹配 {row['name']}..."

            score, reasons = matcher.match(
                profile_data,
                row,
                professor_embedding=row["embedding"],
                profile_embedding=profile_vec,
                language=match_reason_lang,
            )
            pending.append((row["id"], score, reasons))
            task.success_count += 1

            if len(pending) >= _MATCH_WRITE_BATCH:
                _persist_match_records(db, profile_id, pending)
                pending.clear()
                persist_task(task)

        _persist_match_records(db, profile_id, pending)

        if not task.cancel_requested:
            task.message = f"匹配完成，共 {task.success_count} 位教授"
        _finalize(task)

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"匹配失败: {str(e)}"
        persist_task(task)


@register_task("single-letter")
def execute_single_letter(
    task_id: str,
    professor_id: int,
    profile_id: int,
    user_id: int,
    language: str,
) -> None:
    """Generate a contact letter for one professor."""
    from ..db.database import get_db
    from ..models.schema import MatchRecord, Professor, UserProfile, UserSettings
    from ..ai_workflows.workflows import generate_letter

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    persist_task(task)
    db = get_db()

    try:
        with db.session() as session:
            user_settings = (
                session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            )
            provider = _llm_provider_for_user_settings_row(user_settings)
            result = (
                session.query(MatchRecord, Professor, UserProfile)
                .join(Professor, MatchRecord.professor_id == Professor.id)
                .join(UserProfile, MatchRecord.user_profile_id == UserProfile.id)
                .filter(
                    MatchRecord.user_profile_id == profile_id,
                    MatchRecord.professor_id == professor_id,
                )
                .first()
            )
            if not result:
                task.status = TaskStatus.FAILED
                task.error_message = "未找到匹配记录，请先运行匹配"
                persist_task(task)
                return

            match_record, professor, profile = result
            task.message = f"正在为 {professor.name} 生成邮件..."

            from .experience_pool_service import format_pool_stories_summary

            experience_stories = ""
            if profile.experience_pool_id:
                experience_stories = format_pool_stories_summary(
                    session,
                    profile.experience_pool_id,
                    language=language if language in ("zh", "en") else "en",
                )

            profile_data = {
                "name": profile.name,
                "name_locales": profile.name_locales or {},
                "education": profile.education or [],
                "research_experience": profile.research_experience or [],
                "projects": profile.projects or [],
                "skills": profile.skills or [],
                "academic_profile": profile.academic_profile,
                "profile_analysis": profile.profile_analysis or {},
                "experience_stories": experience_stories,
            }
            prof_data = {
                "name": professor.name,
                "name_locales": professor.name_locales or {},
                "affiliation": professor.affiliation,
                "research_interests": professor.research_interests or [],
                "publications": professor.publications or [],
                "research_profile": professor.research_profile,
                "research_profile_analysis": professor.research_profile_analysis or {},
            }
            reasons = match_record.match_reasons or []

        if task.cancel_requested:
            task.status = TaskStatus.CANCELLED
            persist_task(task)
            return

        letter_content = generate_letter(
            student_info=profile_data,
            professor_info=prof_data,
            match_reasons=reasons,
            language=language,
            provider=provider,
            cancel_checker=lambda: task.cancel_requested,
        )

        if task.cancel_requested:
            task.status = TaskStatus.CANCELLED
            persist_task(task)
            return

        with db.session() as session:
            mr = (
                session.query(MatchRecord)
                .filter(
                    MatchRecord.user_profile_id == profile_id,
                    MatchRecord.professor_id == professor_id,
                )
                .first()
            )
            if mr:
                mr.letter_content = letter_content
                mr.letter_generated_at = datetime.now(timezone.utc)

        task.success_count = 1
        task.current = 1
        task.message = f"邮件生成完成：{prof_data['name']}"
        task.status = TaskStatus.COMPLETED
        persist_task(task)

    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        task.message = "邮件生成已取消"
        persist_task(task)
    except Exception as e:
        from ..ai_workflows.provider import LLMCancelled

        if isinstance(e, LLMCancelled):
            task.status = TaskStatus.CANCELLED
            task.message = "邮件生成已取消"
            persist_task(task)
            return
        task.status = TaskStatus.FAILED
        task.error_message = f"生成失败: {str(e)}"
        persist_task(task)


@register_task("university-crawl")
def execute_university_crawl(task_id: str, university_id: str) -> None:
    """Crawl all professors from a registered university department website.

    Runs the university-specific crawler synchronously (blocking network I/O),
    then persists each professor to the database, skipping duplicates.
    """
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.universities.registry import get_crawler

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在初始化爬虫..."
    persist_task(task)
    db = get_db()

    try:
        crawler = get_crawler(university_id)
    except KeyError:
        task.status = TaskStatus.FAILED
        task.error_message = f"未找到院校爬虫: {university_id}"
        persist_task(task)
        return

    if task.cancel_requested:
        task.status = TaskStatus.CANCELLED
        persist_task(task)
        return

    task.message = f"正在爬取 {crawler.display_name}..."

    try:
        professors_data: list[dict] = crawler.crawl_all()
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"爬取失败: {str(e)}"
        persist_task(task)
        return

    total = len(professors_data)
    task.total = total
    task.message = f"共获取 {total} 条记录，正在入库..."
    new_professor_ids: List[int] = []

    from ..models.schema import University
    from ..utils.professor_dedup import find_matching_professor
    from ..utils.url_utils import normalize_school_crawl_professors

    crawl_base = getattr(crawler, "crawl_base_url", "") or ""
    normalize_school_crawl_professors(professors_data, crawl_base)

    with db.session() as session:
        user_universities = (
            session.query(University)
            .filter(University.user_id == task.user_id)
            .all()
        )

    for i, prof_data in enumerate(professors_data):
        if i < task.current:
            continue  # already processed before an interruption; resuming
        if task.cancel_requested:
            break

        task.current = i + 1
        task.message = f"正在保存第 {i + 1}/{total} 位: {prof_data.get('name', '')}"

        try:
            with db.session() as session:
                affiliation_val = prof_data.get("affiliation")
                existing = find_matching_professor(
                    session,
                    task.user_id,
                    prof_data["name"],
                    affiliation_val,
                    universities=user_universities,
                )
                if existing:
                    task.results.append(
                        {"name": prof_data["name"], "success": True, "skipped": True}
                    )
                    continue

                professor = Professor(
                    user_id=task.user_id,
                    name=prof_data["name"],
                    affiliation=affiliation_val or None,
                    email=prof_data.get("email"),
                    homepage=prof_data.get("homepage"),
                    research_interests=prof_data.get("research_interests", []),
                    publications=[],
                )
                session.add(professor)
                session.flush()
                new_professor_ids.append(professor.id)

            task.success_count += 1
            task.results.append({"name": prof_data["name"], "success": True, "skipped": False})

        except Exception as e:
            task.failed_count += 1
            task.results.append(
                {"name": prof_data.get("name", "?"), "success": False, "error": str(e)}
            )

    will_complete = not task.cancel_requested
    if will_complete:
        skipped = sum(1 for r in task.results if r.get("skipped"))
        task.message = f"完成！新增 {task.success_count} 位，跳过重复 {skipped} 位，失败 {task.failed_count} 位"
    _finalize(task)
    if will_complete and new_professor_ids:
        _enqueue_batch_professor_enrichment_if_enabled(
            task.user_id, new_professor_ids, parent_task_id=task.task_id
        )


def _enqueue_batch_professor_enrichment_if_enabled(
    user_id: int, professor_ids: List[int], *, parent_task_id: Optional[str] = None
) -> None:
    """Chain batch enrichment when user auto-enrich flags are on."""
    if not professor_ids:
        return
    from ..db.database import get_db
    from ..models.schema import UserSettings

    db = get_db()
    with db.session() as session:
        row = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == user_id)
            .first()
        )
        enrich_flags = flags_from_user_settings_row(row)
    if not any_auto_enrich_substep_enabled(enrich_flags):
        return
    batch_enrich = create_task(
        "batch-professor-enrichment",
        f"教授信息增强 ({len(professor_ids)} 位)",
        user_id,
        total=len(professor_ids),
        parent_task_id=parent_task_id,
    )
    enqueue_task(
        "batch-professor-enrichment",
        batch_enrich.task_id,
        professor_ids=professor_ids,
    )


def _mark_pending_dblp_professors_not_found(user_id: int, professor_ids: List[int]) -> int:
    from ..db.database import get_db
    from ..models.schema import Professor

    db = get_db()
    cleared = 0
    with db.session() as session:
        for pid in professor_ids:
            professor = (
                session.query(Professor)
                .filter(Professor.id == pid, Professor.user_id == user_id)
                .first()
            )
            if professor and professor.dblp_enrichment_status == "pending":
                professor.dblp_enrichment_status = "not_found"
                cleared += 1
    return cleared


@register_task("batch-dblp-match")
def execute_batch_dblp_match(
    task_id: str,
    professor_ids: List[int],
    university_variants: List[str],
    department_affiliation: str | None = None,
) -> None:
    """Match professors to DBLP profiles."""
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.dblp import DblpClient, dblp_profile_url
    from ..crawler.dblp_matcher import match_professor_dblp

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = len(professor_ids) if professor_ids else 1
    persist_task(task)

    if not professor_ids:
        task.status = TaskStatus.COMPLETED
        task.message = "无教授需要匹配 DBLP"
        persist_task(task)
        return

    db = get_db()
    with db.session() as session:
        row = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == task.user_id)
            .first()
        )
        request_delay = (
            row.request_delay if row and row.request_delay else app_settings.request_delay
        )

    dblp_client = DblpClient(request_delay=request_delay)
    matched_ids: List[int] = []

    def _finish_cancelled() -> None:
        cleared = _mark_pending_dblp_professors_not_found(task.user_id, professor_ids)
        task.status = TaskStatus.CANCELLED
        task.message = (
            f"DBLP 匹配已取消（{cleared} 位未完成的教授已标记为未找到）"
            if cleared
            else "DBLP 匹配已取消"
        )
        persist_task(task)

    for i, pid in enumerate(professor_ids):
        if i < task.current:
            continue
        if task.cancel_requested:
            _finish_cancelled()
            return

        task.current = i + 1
        with db.session() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == pid, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                task.failed_count += 1
                continue
            prof_name = professor.name
            crawled_email = professor.email

        task.message = f"正在搜索 {prof_name} 的 DBLP 主页 ({i + 1}/{len(professor_ids)})"

        try:
            match_result = match_professor_dblp(
                chinese_name=prof_name,
                crawled_email=crawled_email,
                university_variants=university_variants,
                department_affiliation=department_affiliation,
                dblp_client=dblp_client,
                request_delay=request_delay,
                cancel_checker=lambda: task.cancel_requested,
            )
        except Exception as e:
            logger.warning("DBLP matching failed for %s: %s", prof_name, e)
            match_result = {"status": "not_found", "dblp_pid": None, "candidates": []}

        with db.session() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == pid, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                continue
            if match_result.get("status") == "matched":
                pid_val = match_result["dblp_pid"]
                author_data = dblp_client.get_author(pid_val)
                professor.dblp_pid = pid_val
                professor.dblp_url = match_result.get("dblp_url") or dblp_profile_url(pid_val)
                professor.dblp_enrichment_status = "matched"
                if author_data:
                    from ..utils.publication_merge import merge_publications

                    professor.publications = merge_publications(
                        professor.publications,
                        author_data.get("publications") or [],
                        "dblp",
                    )
                    from ..utils.profile_merge import apply_external_affiliation

                    apply_external_affiliation(professor, author_data.get("affiliation"))
                from ..utils.name_locales import apply_dblp_name_update

                en_name = match_result.get("dblp_name") or (
                    author_data.get("name") if author_data else None
                )
                apply_dblp_name_update(professor, en_name)
                matched_ids.append(pid)
            elif match_result.get("status") == "ambiguous":
                professor.dblp_enrichment_status = "ambiguous"
                professor.dblp_candidates = match_result.get("candidates", [])
            else:
                professor.dblp_enrichment_status = "not_found"

        task.success_count += 1
        task.results.append(
            {
                "professor_id": pid,
                "name": prof_name,
                "success": True,
                "dblp_status": match_result.get("status"),
            }
        )

        if (
            not task.cancel_requested
            and i < len(professor_ids) - 1
            and request_delay > 0
        ):
            time.sleep(request_delay)

    if task.cancel_requested:
        _finish_cancelled()
        return

    matched = sum(1 for r in task.results if r.get("dblp_status") == "matched")
    ambiguous = sum(1 for r in task.results if r.get("dblp_status") == "ambiguous")
    task.message = (
        f"DBLP 匹配完成：自动匹配 {matched} 位，待确认 {ambiguous} 位，"
        f"未找到 {task.success_count - matched - ambiguous} 位"
    )
    _finalize(task)
    if matched_ids and task.status == TaskStatus.COMPLETED:
        _enqueue_batch_professor_enrichment_if_enabled(
            task.user_id, matched_ids, parent_task_id=task.task_id
        )


@register_task("single-dblp-crawl")
def execute_single_dblp_crawl(task_id: str, dblp_url: str) -> None:
    """Crawl DBLP profile and merge publications into professor record."""
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.dblp import DblpClient
    from ..utils.publication_merge import merge_publications

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在爬取 DBLP 教授信息..."
    persist_task(task)

    db = get_db()
    try:
        pid = extract_dblp_pid_from_url(dblp_url)
        client = DblpClient()
        author_data = client.get_author(pid)
        if not author_data:
            task.status = TaskStatus.FAILED
            task.error_message = "未找到该 DBLP 学者信息"
            persist_task(task)
            return

        if task.cancel_requested:
            task.status = TaskStatus.CANCELLED
            persist_task(task)
            return

        profile_url = author_data.get("dblp_url") or dblp_url
        with db.session() as session:
            existing = (
                session.query(Professor)
                .filter(
                    Professor.user_id == task.user_id,
                    Professor.dblp_pid == author_data["dblp_pid"],
                )
                .first()
            )
            if existing:
                professor = existing
                from ..utils.profile_merge import apply_external_affiliation
                from ..utils.name_locales import apply_dblp_name_update

                apply_dblp_name_update(professor, author_data.get("name"))
                apply_external_affiliation(professor, author_data.get("affiliation"))
                professor.dblp_url = profile_url
                professor.publications = merge_publications(
                    professor.publications,
                    author_data.get("publications") or [],
                    "dblp",
                )
            else:
                professor = Professor(
                    user_id=task.user_id,
                    name=author_data["name"],
                    affiliation=author_data.get("affiliation"),
                    dblp_pid=author_data["dblp_pid"],
                    dblp_url=profile_url,
                    publications=merge_publications(
                        [], author_data.get("publications") or [], "dblp"
                    ),
                    source="dblp",
                )
                from ..utils.name_locales import (
                    apply_inferred_locales_from_name,
                    merge_name_locales,
                )

                apply_inferred_locales_from_name(professor)
                merge_name_locales(professor, en=author_data.get("name"))
                session.add(professor)

            session.flush()
            enrichment_professor_id = professor.id
            settings_row = (
                session.query(UserSettings)
                .filter(UserSettings.user_id == task.user_id)
                .first()
            )
            enrich_flags = flags_from_user_settings_row(settings_row)
            enrich_planned = planned_enrichment_step_count_for_professor(
                professor, enrich_flags
            )

        task.success_count = 1
        task.current = 1
        task.message = f"DBLP 爬取完成：{author_data['name']}"
        task.results.append({"name": author_data["name"], "success": True})
        task.status = TaskStatus.COMPLETED
        persist_task(task)

        if enrich_planned > 0:
            enrich_task = create_task(
                "professor-enrichment",
                "教授信息增强",
                task.user_id,
                total=enrich_planned,
                parent_task_id=task.task_id,
            )
            enqueue_task(
                "professor-enrichment",
                enrich_task.task_id,
                professor_id=enrichment_professor_id,
            )
    except ValueError as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        persist_task(task)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"DBLP 爬取失败: {str(e)}"
        persist_task(task)


@register_task("batch-dblp-crawl")
def execute_batch_dblp_crawl(task_id: str, dblp_urls: List[str]) -> None:
    """Crawl multiple DBLP profile URLs."""
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.dblp import DblpClient, extract_dblp_pid_from_url
    from ..crawler.dblp import dblp_profile_url
    from ..utils.publication_merge import merge_publications

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    persist_task(task)
    db = get_db()
    client = DblpClient()
    new_professor_ids: List[int] = []

    for i, url in enumerate(dblp_urls):
        if i < task.current:
            continue
        if task.cancel_requested:
            break
        task.current = i + 1
        task.message = f"正在爬取 DBLP 第 {i + 1}/{task.total} 个..."
        try:
            pid = extract_dblp_pid_from_url(url)
            author_data = client.get_author(pid)
            if not author_data:
                task.failed_count += 1
                continue
            with db.session() as session:
                existing = (
                    session.query(Professor)
                    .filter(
                        Professor.user_id == task.user_id,
                        Professor.dblp_pid == author_data["dblp_pid"],
                    )
                    .first()
                )
                if existing:
                    task.results.append({"url": url, "success": True, "skipped": True})
                    continue
                professor = Professor(
                    user_id=task.user_id,
                    name=author_data["name"],
                    affiliation=author_data.get("affiliation"),
                    dblp_pid=author_data["dblp_pid"],
                    dblp_url=author_data.get("dblp_url") or dblp_profile_url(pid),
                    publications=merge_publications(
                        [], author_data.get("publications") or [], "dblp"
                    ),
                    source="dblp",
                )
                from ..utils.name_locales import (
                    apply_inferred_locales_from_name,
                    merge_name_locales,
                )

                apply_inferred_locales_from_name(professor)
                merge_name_locales(professor, en=author_data.get("name"))
                session.add(professor)
                session.flush()
                new_professor_ids.append(professor.id)
            task.success_count += 1
            task.results.append({"url": url, "name": author_data["name"], "success": True})
        except Exception as e:
            task.failed_count += 1
            task.results.append({"url": url, "success": False, "error": str(e)})

    will_complete = not task.cancel_requested
    _finalize(task)
    if will_complete and new_professor_ids and task.status == TaskStatus.COMPLETED:
        _enqueue_batch_professor_enrichment_if_enabled(
            task.user_id, new_professor_ids, parent_task_id=task.task_id
        )


@register_task("generic-university-crawl")
def execute_generic_university_crawl(task_id: str, config_id: int, cache_key: str | None = None) -> None:
    """Crawl professors using a user-defined UniversityCrawlerConfig.

    Loads the config from DB, runs GenericUniversityCrawler, persists professors.
    When the config is linked to a University with name variants, enqueues a
    separate ``batch-dblp-match`` task for DBLP linking.

    If *cache_key* is provided and the test crawl cache is still valid, the
    cached results are used instead of re-crawling the website.
    """
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings, UniversityCrawlerConfig, University

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在初始化爬虫..."
    persist_task(task)
    db = get_db()

    # Load config from DB
    with db.session() as session:
        config_row = (
            session.query(UniversityCrawlerConfig)
            .filter(
                UniversityCrawlerConfig.id == config_id,
                UniversityCrawlerConfig.user_id == task.user_id,
            )
            .first()
        )
        if not config_row:
            task.status = TaskStatus.FAILED
            task.error_message = "爬虫配置不存在"
            persist_task(task)
            return

        # Extract all config fields while session is open
        config_data = {
            "id": config_row.id,
            "name": config_row.name,
            "university": config_row.university,
            "department": config_row.department,
            "list_url": config_row.list_url,
            "extraction_mode": config_row.extraction_mode,
            "css_selectors": config_row.css_selectors or {},
            "affiliation": config_row.affiliation,
            "university_id": config_row.university_id,
        }

        # Load university name variants if linked
        university_variants: list[str] = []
        university_full_name: str | None = None
        if config_row.university_id:
            uni = (
                session.query(University)
                .filter(University.id == config_row.university_id)
                .first()
            )
            if uni:
                university_variants = list(uni.name_variants or [])
                university_full_name = uni.full_name

        # Get API key for LLM mode
        user_settings = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == task.user_id)
            .first()
        )
        from ..llm.config import resolve_llm_config

        llm_config = resolve_llm_config(user_settings, app_settings)
        request_delay = float(
            user_settings.request_delay if user_settings and user_settings.request_delay is not None
            else app_settings.request_delay
        )

    # Import and create crawler
    from ..crawler.crawl4ai_engine.generic_crawler import GenericUniversityCrawler

    # Try to reuse test crawl cache to avoid re-fetching pages
    professors_data: list[dict] | None = None
    if cache_key:
        from .routes.professors import get_cached_test_results
        cached = get_cached_test_results(cache_key)
        if cached is not None:
            professors_data = cached
            task.message = f"复用测试爬取结果（{len(cached)} 条），正在处理..."

    if professors_data is None:
        crawler = GenericUniversityCrawler(
            university_id=f"custom-{config_data['id']}",
            display_name=config_data["name"],
            list_url=config_data["list_url"],
            extraction_mode=config_data["extraction_mode"],
            css_selectors=config_data["css_selectors"],
            affiliation=config_data["affiliation"] or config_data["university"],
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            model=llm_config.model,
            llm_provider=llm_config.provider,
        )

        task.message = f"正在爬取 {crawler.display_name}..."

        try:
            professors_data = crawler.crawl_all(
                delay=request_delay,
                send_progress=lambda m: setattr(task, "message", m),
                cancel_checker=lambda: task.cancel_requested,
            )
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = f"爬取失败: {str(e)}"
            persist_task(task)
            return

    if task.cancel_requested:
        task.status = TaskStatus.CANCELLED
        persist_task(task)
        return

    total = len(professors_data)
    if total == 0:
        task.status = TaskStatus.FAILED
        if config_data["extraction_mode"] == "llm":
            task.error_message = "AI 提取未返回结果，请检查 LLM API Key 与模型配置是否正确，或切换为 CSS 选择器模式重试"
        else:
            task.error_message = "未提取到教授信息，请检查 CSS 选择器配置是否正确"
        task.message = "爬取失败"
        persist_task(task)
        return

    from ..utils.url_utils import normalize_school_crawl_professors

    normalize_school_crawl_professors(professors_data, config_data["list_url"])

    do_dblp_match = bool(university_variants)
    logger.info(
        "DBLP matching decision: do_dblp_match=%s, university_variants=%s (university_id=%s)",
        do_dblp_match, university_variants, config_data["university_id"],
    )
    task.total = total
    if do_dblp_match:
        task.message = f"共获取 {total} 条记录，正在入库（DBLP 匹配将另起任务）..."
    else:
        if not config_data["university_id"]:
            skip_reason = "爬虫配置未关联大学，已跳过 DBLP 自动匹配。请在设置中将爬虫配置关联到一个大学"
        else:
            skip_reason = "关联大学缺少名称变体（name_variants），已跳过 DBLP 自动匹配。请编辑大学信息补充名称变体"
        logger.warning("%s (config_id=%s)", skip_reason, config_data["id"])
        task.message = f"共获取 {total} 条记录，正在入库...（注意：{skip_reason}）"

    new_professor_ids: list[int] = []
    department_affiliation = config_data["affiliation"]

    from ..utils.professor_dedup import find_matching_professor

    with db.session() as session:
        crawl_universities = (
            session.query(University)
            .filter(University.user_id == task.user_id)
            .all()
        )

    for i, prof_data in enumerate(professors_data):
        if i < task.current:
            continue
        if task.cancel_requested:
            break

        task.current = i + 1
        prof_name = prof_data.get("name", "")
        task.message = f"正在处理第 {i + 1}/{total} 位: {prof_name}"

        try:
            with db.session() as session:
                affiliation_val = prof_data.get("affiliation")
                existing = find_matching_professor(
                    session,
                    task.user_id,
                    prof_name,
                    affiliation_val,
                    university_variants=university_variants,
                    university_full_name=university_full_name,
                    department_affiliation=department_affiliation,
                    universities=crawl_universities,
                )
                if existing:
                    task.results.append(
                        {"name": prof_name, "success": True, "skipped": True}
                    )
                    continue

            with db.session() as session:
                professor = Professor(
                    user_id=task.user_id,
                    name=prof_name,
                    affiliation=prof_data.get("affiliation"),
                    email=prof_data.get("email"),
                    homepage=prof_data.get("homepage"),
                    research_interests=prof_data.get("research_interests", []),
                    manual_notes=prof_data.get("manual_notes"),
                    publications=[],
                    source="school_crawler",
                    dblp_enrichment_status="pending" if do_dblp_match else None,
                )
                from ..utils.name_locales import apply_inferred_locales_from_name

                apply_inferred_locales_from_name(professor)
                session.add(professor)
                session.flush()
                new_professor_ids.append(professor.id)

            task.success_count += 1
            task.results.append({"name": prof_name, "success": True, "skipped": False})

        except Exception as e:
            task.failed_count += 1
            task.results.append(
                {"name": prof_name, "success": False, "error": str(e)}
            )

    will_complete = not task.cancel_requested
    if will_complete:
        skipped = sum(1 for r in task.results if r.get("skipped"))
        task.message = (
            f"完成！新增 {task.success_count} 位，跳过重复 {skipped} 位，失败 {task.failed_count} 位"
        )
        if do_dblp_match and new_professor_ids:
            dblp_task = create_task(
                "batch-dblp-match",
                f"DBLP 匹配 ({len(new_professor_ids)} 位)",
                task.user_id,
                total=len(new_professor_ids),
                parent_task_id=task.task_id,
            )
            enqueue_task(
                "batch-dblp-match",
                dblp_task.task_id,
                professor_ids=new_professor_ids,
                university_variants=university_variants,
                department_affiliation=department_affiliation,
            )
            task.message += f"，已启动 DBLP 匹配任务（{len(new_professor_ids)} 位）"
    _finalize(task)


def _enrich_professor_core(
    user_id: int,
    professor_id: int,
    *,
    flags: AutoEnrichFlags,
    progress: Optional[Callable[[str], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
    on_substep_done: Optional[Callable[[], None]] = None,
) -> str:
    """Fill top-N publication abstracts, English summaries, research profile. Returns professor name."""
    from sqlalchemy.orm.attributes import flag_modified

    from ..config import settings as app_settings
    from ..crawler.scholar import ScholarCrawler
    from ..db.database import get_db
    from ..ai_workflows.provider import LLMProvider
    from ..ai_workflows.source_helpers import (
        build_paper_summary_from_dblp_publication,
        build_paper_summary_from_scholar_publication,
    )
    from ..ai_workflows.workflows import generate_professor_profile
    from ..models.schema import Professor, UserSettings
    from .source_input_service import keep_non_scholar_paper_summaries

    def _prog(msg: str) -> None:
        if progress:
            progress(msg)

    def _cancelled() -> bool:
        return bool(cancel_checker and cancel_checker())

    def _bump() -> None:
        if on_substep_done:
            on_substep_done()

    db = get_db()
    max_pub = app_settings.professor_enrichment_max_publications

    with db.session() as session:
        professor = (
            session.query(Professor)
            .filter(Professor.id == professor_id, Professor.user_id == user_id)
            .first()
        )
        if not professor:
            raise ValueError("教授不存在或无权限")
        has_scholar = bool(professor.google_scholar_id)
        has_dblp = bool(professor.dblp_pid)
        publications = list(professor.publications or [])
        prof_name = professor.name

    provider: Optional[LLMProvider] = None

    def _ensure_provider() -> LLMProvider:
        nonlocal provider
        if provider is None:
            with db.session() as session:
                user_settings = (
                    session.query(UserSettings)
                    .filter(UserSettings.user_id == user_id)
                    .first()
                )
                provider = _llm_provider_for_user_settings_row(user_settings)
        return provider

    if _cancelled():
        raise TaskCancelled()

    if flags.fetch_publication_details and has_scholar and publications:
        _prog("正在获取论文详情...")
        crawler = ScholarCrawler()
        for i in range(min(len(publications), max_pub)):
            if _cancelled():
                raise TaskCancelled()
            pub = publications[i]
            if pub.get("author_pub_id") and not (pub.get("abstract") or "").strip():
                try:
                    details = crawler.fill_publication(pub["author_pub_id"])
                    publications[i].update(details)
                except Exception:
                    pass
                threading.Event().wait(timeout=app_settings.request_delay)

        with db.session() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == user_id)
                .first()
            )
            if professor:
                professor.publications = publications
                flag_modified(professor, "publications")
                professor.embedding = None
        _bump()

    if _cancelled():
        raise TaskCancelled()

    if flags.paper_summaries and publications:
        _prog("正在生成论文摘要...")
        prov = _ensure_provider()
        with db.session() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == user_id)
                .first()
            )
            if not professor:
                raise ValueError("教授不存在或无权限")
            from .source_input_service import keep_paper_summaries_excluding

            publications = list(professor.publications or [])
            merged = keep_paper_summaries_excluding(
                professor.paper_summaries or [], {"scholar_pub", "dblp_pub"}
            )
            new_items: list = []
            for pub in publications[:max_pub]:
                if _cancelled():
                    raise TaskCancelled()
                src = pub.get("source")
                if not src:
                    if pub.get("dblp_url"):
                        src = "dblp"
                    elif pub.get("author_pub_id") or pub.get("gscholar_url"):
                        src = "scholar"
                    else:
                        src = "scholar"
                if src == "dblp":
                    new_items.append(
                        build_paper_summary_from_dblp_publication(
                            pub, provider=prov, language="en"
                        )
                    )
                else:
                    new_items.append(
                        build_paper_summary_from_scholar_publication(
                            pub, provider=prov, language="en"
                        )
                    )
            professor.paper_summaries = merged + new_items
            flag_modified(professor, "paper_summaries")
            professor.embedding = None
        _bump()

    if _cancelled():
        raise TaskCancelled()

    if flags.research_profile:
        _prog("正在生成科研画像...")
        prov = _ensure_provider()
        with db.session() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == user_id)
                .first()
            )
            if not professor:
                raise ValueError("教授不存在或无权限")
            prof_data = {
                "name": professor.name,
                "affiliation": professor.affiliation,
                "research_interests": professor.research_interests or [],
                "publications": professor.publications or [],
                "paper_summaries": professor.paper_summaries or [],
                "manual_notes": professor.manual_notes,
                "homepage": professor.homepage,
                "google_scholar_url": professor.google_scholar_url,
            }
            prof_name = professor.name

        result = generate_professor_profile(prof_data, language="en", provider=prov)

        with db.session() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == user_id)
                .first()
            )
            if not professor:
                raise ValueError("教授不存在或无权限")
            professor.research_profile = result.research_profile
            professor.research_profile_analysis = result.research_profile_analysis
            professor.research_profile_sources = result.research_profile_sources
            professor.research_profile_evidence = result.research_profile_evidence
            professor.research_profile_conflicts = result.research_profile_conflicts
            professor.research_profile_generated_at = datetime.now(timezone.utc)
            professor.embedding = None
        _bump()

    return prof_name


@register_task("professor-enrichment")
def execute_professor_enrichment(task_id: str, professor_id: int) -> None:
    """Background task: publication fill, paper summaries, research profile."""
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    persist_task(task)

    db = get_db()
    with db.session() as session:
        settings_row = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == task.user_id)
            .first()
        )
        flags = flags_from_user_settings_row(settings_row)
        professor = (
            session.query(Professor)
            .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
            .first()
        )
        if not professor:
            task.status = TaskStatus.FAILED
            task.error_message = "教授不存在或无权限"
            task.message = "教授信息增强失败"
            persist_task(task)
            return

        planned = planned_enrichment_step_count_for_professor(professor, flags)
        prof_name = professor.name

    task.total = planned
    task.current = 0
    persist_task(task)

    if planned == 0:
        task.success_count = 1
        task.current = 0
        task.message = "教授信息增强已跳过（未启用子步或当前数据无可执行步骤）"
        task.results.append(
            {
                "success": True,
                "professor_id": professor_id,
                "name": prof_name,
                "skipped": True,
            }
        )
        task.status = TaskStatus.COMPLETED
        persist_task(task)
        return

    def _bump_current() -> None:
        task.current += 1
        persist_task(task)

    try:
        name = _enrich_professor_core(
            task.user_id,
            professor_id,
            flags=flags,
            progress=lambda m: setattr(task, "message", m),
            cancel_checker=lambda: task.cancel_requested,
            on_substep_done=_bump_current,
        )
        task.success_count = 1
        task.current = planned
        task.results.append(
            {"success": True, "professor_id": professor_id, "name": name}
        )
        task.message = f"教授信息增强完成：{name}"
        _finalize(task)
    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        persist_task(task)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"教授信息增强失败: {str(e)}"
        task.message = "教授信息增强失败"
        persist_task(task)


@register_task("batch-professor-enrichment")
def execute_batch_professor_enrichment(task_id: str, professor_ids: List[int]) -> None:
    """Sequential enrichment for many professors (one DB user)."""
    from ..db.database import get_db
    from ..models.schema import UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = len(professor_ids) if professor_ids else 1
    persist_task(task)

    if not professor_ids:
        task.status = TaskStatus.COMPLETED
        task.message = "无教授需要增强"
        persist_task(task)
        return

    db = get_db()
    # Hoist UserSettings query out of loop — flags don't change between iterations
    with db.session() as session:
        _settings_row = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == task.user_id)
            .first()
        )
        _flags = flags_from_user_settings_row(_settings_row)

    for i, pid in enumerate(professor_ids):
        if i < task.current:
            continue
        if task.cancel_requested:
            break
        task.current = i + 1
        task.message = f"正在增强第 {i + 1}/{len(professor_ids)} 位教授..."
        try:
            _enrich_professor_core(
                task.user_id,
                pid,
                flags=_flags,
                progress=lambda m: setattr(task, "message", m),
                cancel_checker=lambda: task.cancel_requested,
            )
            task.success_count += 1
            task.results.append({"professor_id": pid, "success": True})
        except TaskCancelled:
            break
        except Exception as exc:
            task.failed_count += 1
            task.results.append({"professor_id": pid, "success": False, "error": str(exc)})

    if not task.cancel_requested and task.success_count == 0 and task.failed_count > 0:
        task.status = TaskStatus.FAILED
        task.error_message = "批量教授信息增强失败"
        task.message = f"失败：成功 {task.success_count}，失败 {task.failed_count}"
        persist_task(task)
        return
    if not task.cancel_requested:
        task.message = f"批量教授信息增强完成：成功 {task.success_count}，失败 {task.failed_count}"
    _finalize(task)


@register_task("paper-summary")
def execute_professor_source_summary(
    task_id: str,
    professor_id: int,
    source_input_ids: list[int],
) -> None:
    """Summarize selected source inputs and persist paper summaries."""
    from sqlalchemy.orm.attributes import flag_modified

    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..ai_workflows.provider import LLMProvider
    from ..ai_workflows.source_helpers import build_paper_summary_from_source
    from ..models.schema import Professor, SourceInput, UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在准备论文总结任务..."
    persist_task(task)
    db = get_db()

    if not source_input_ids:
        task.status = TaskStatus.FAILED
        task.error_message = "请先选择需要总结的来源输入"
        persist_task(task)
        return

    with db.session() as session:
        professor = (
            session.query(Professor)
            .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
            .first()
        )
        if not professor:
            task.status = TaskStatus.FAILED
            task.error_message = "教授不存在或无权限"
            persist_task(task)
            return

        user_settings = (
            session.query(UserSettings).filter(UserSettings.user_id == task.user_id).first()
        )
        provider = _llm_provider_for_user_settings_row(user_settings)

    for idx, source_id in enumerate(source_input_ids, start=1):
        if idx - 1 < task.current:
            continue
        if task.cancel_requested:
            break

        task.current = idx
        task.message = f"正在总结第 {idx}/{len(source_input_ids)} 篇论文..."
        try:
            with db.session() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                source = (
                    session.query(SourceInput)
                    .filter(SourceInput.id == source_id, SourceInput.user_id == task.user_id)
                    .first()
                )
                if not professor or not source:
                    task.failed_count += 1
                    task.results.append(
                        {"source_input_id": source_id, "success": False, "error": "来源输入不存在"}
                    )
                    continue

                summary = build_paper_summary_from_source(
                    {
                        "id": source.id,
                        "source_type": source.source_type,
                        "title": source.title,
                        "original_name": source.original_name,
                        "canonical_id": source.canonical_id,
                        "abstract": source.abstract,
                        "extracted_markdown": source.extracted_markdown,
                        "extracted_text": source.extracted_text,
                    },
                    provider=provider,
                    language="en",
                )
                if not summary:
                    task.failed_count += 1
                    task.results.append(
                        {"source_input_id": source_id, "success": False, "error": "无法生成论文总结"}
                    )
                    continue

                existing = list(professor.paper_summaries or [])
                replaced = False
                for i, item in enumerate(existing):
                    if item.get("source_input_id") == summary.get("source_input_id"):
                        existing[i] = summary
                        replaced = True
                        break
                if not replaced:
                    existing.append(summary)
                professor.paper_summaries = existing
                flag_modified(professor, "paper_summaries")

                if source.source_type == "arxiv" and source.title:
                    publications = list(professor.publications or [])
                    titles = {p.get("title") for p in publications}
                    if source.title not in titles:
                        publications.append(
                            {
                                "title": source.title,
                                "year": None,
                                "citations": None,
                                "authors": None,
                            }
                        )
                    professor.publications = publications
                    flag_modified(professor, "publications")

                source.professor_id = professor.id
                professor.embedding = None

            task.success_count += 1
            task.results.append({"source_input_id": source_id, "success": True})
        except Exception as exc:
            task.failed_count += 1
            task.results.append({"source_input_id": source_id, "success": False, "error": str(exc)})

    if not task.cancel_requested and task.success_count == 0 and task.failed_count > 0:
        task.status = TaskStatus.FAILED
        task.error_message = "论文总结失败，请检查任务详情后重试"
        task.message = f"论文总结失败：成功 {task.success_count}，失败 {task.failed_count}"
        persist_task(task)
        return

    if not task.cancel_requested:
        task.message = f"论文总结完成：成功 {task.success_count}，失败 {task.failed_count}"
    _finalize(task)


@register_task("professor-profile")
def execute_professor_profile_generation(
    task_id: str,
    *,
    professor_id: int,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Generate a research profile for a single professor."""
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..ai_workflows.provider import LLMProvider
    from ..ai_workflows.workflows import generate_professor_profile
    from ..models.schema import Professor, UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.current = 0
    task.total = 3
    task.message = "正在准备教授数据..."
    persist_task(task)

    try:
        if session_factory is None:
            session_context = get_db().session
        else:

            def session_context():
                return _session_scope(session_factory)

        with session_context() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                task.status = TaskStatus.FAILED
                task.error_message = "教授不存在或无权限"
                persist_task(task)
                return

            prof_data = {
                "name": professor.name,
                "affiliation": professor.affiliation,
                "research_interests": professor.research_interests or [],
                "publications": professor.publications or [],
                "paper_summaries": professor.paper_summaries or [],
                "manual_notes": professor.manual_notes,
                "homepage": professor.homepage,
                "google_scholar_url": professor.google_scholar_url,
            }

            user_settings = (
                session.query(UserSettings).filter(UserSettings.user_id == task.user_id).first()
            )
            provider = _llm_provider_for_user_settings_row(user_settings)

        task.current = 1
        task.message = "正在分析教授科研画像..."
        persist_task(task)

        if task.cancel_requested:
            raise TaskCancelled()

        result = generate_professor_profile(prof_data, language="en", provider=provider)
        task.current = 2
        task.message = "正在保存教授科研画像..."
        persist_task(task)

        if task.cancel_requested:
            raise TaskCancelled()

        with session_context() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                task.status = TaskStatus.FAILED
                task.error_message = "教授不存在或无权限"
                persist_task(task)
                return

            professor.research_profile = result.research_profile
            professor.research_profile_analysis = result.research_profile_analysis
            professor.research_profile_sources = result.research_profile_sources
            professor.research_profile_evidence = result.research_profile_evidence
            professor.research_profile_conflicts = result.research_profile_conflicts
            professor.research_profile_generated_at = datetime.now(timezone.utc)
            professor.embedding = None

        task.success_count = 1
        task.current = 3
        task.message = f"教授科研画像生成完成：{prof_data['name']}"
        persist_task(task)
        task.results.append(
            {
                "success": True,
                "professor_id": professor_id,
                "name": prof_data["name"],
            }
        )
        task.status = TaskStatus.COMPLETED
        persist_task(task)

    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        task.message = "教授科研画像生成已取消"
        persist_task(task)
    except Exception as e:
        task.failed_count = 1
        task.status = TaskStatus.FAILED
        task.error_message = f"教授画像生成失败: {str(e)}"
        task.message = "教授科研画像生成失败"
        persist_task(task)


@register_task("batch-professor-profiles")
def execute_batch_professor_profiles(
    task_id: str,
    professor_ids: list[int],
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Generate research profiles for a batch of professors."""
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..ai_workflows.provider import LLMProvider
    from ..ai_workflows.workflows import generate_professor_profile
    from ..models.schema import Professor, UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = len(professor_ids)
    persist_task(task)

    if session_factory is None:
        session_context = get_db().session
    else:

        def session_context():
            return _session_scope(session_factory)

    with session_context() as session:
        user_settings = (
            session.query(UserSettings).filter(UserSettings.user_id == task.user_id).first()
        )
        provider = _llm_provider_for_user_settings_row(user_settings)

    for i, professor_id in enumerate(professor_ids):
        if i < task.current:
            continue
        if task.cancel_requested:
            break

        task.current = i + 1
        task.message = f"正在生成第 {i + 1}/{task.total} 位教授科研画像..."

        try:
            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if not professor:
                    task.failed_count += 1
                    task.results.append(
                        {"professor_id": professor_id, "success": False, "error": "教授不存在"}
                    )
                    continue

                prof_data = {
                    "name": professor.name,
                    "affiliation": professor.affiliation,
                    "research_interests": professor.research_interests or [],
                    "publications": professor.publications or [],
                    "paper_summaries": professor.paper_summaries or [],
                    "manual_notes": professor.manual_notes,
                    "homepage": professor.homepage,
                    "google_scholar_url": professor.google_scholar_url,
                }

            result = generate_professor_profile(prof_data, language="en", provider=provider)

            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if not professor:
                    task.failed_count += 1
                    continue

                professor.research_profile = result.research_profile
                professor.research_profile_analysis = result.research_profile_analysis
                professor.research_profile_sources = result.research_profile_sources
                professor.research_profile_evidence = result.research_profile_evidence
                professor.research_profile_conflicts = result.research_profile_conflicts
                professor.research_profile_generated_at = datetime.now(timezone.utc)
                professor.embedding = None

            task.success_count += 1
            task.results.append({"professor_id": professor_id, "name": prof_data["name"], "success": True})

        except Exception as exc:
            task.failed_count += 1
            task.results.append({"professor_id": professor_id, "success": False, "error": str(exc)})

    if not task.cancel_requested and task.success_count == 0 and task.failed_count > 0:
        task.status = TaskStatus.FAILED
        task.error_message = "教授画像生成失败，请检查任务详情后重试"
        task.message = f"教授画像批量生成失败：成功 {task.success_count}，失败 {task.failed_count}"
        persist_task(task)
        return

    if not task.cancel_requested:
        task.message = f"教授科研画像批量生成完成：成功 {task.success_count}，失败 {task.failed_count}"
    _finalize(task)


@register_task("professor-homepage-crawl")
def execute_professor_homepage_crawl(
    task_id: str,
    professor_id: int,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Crawl a professor's homepage URL and merge extracted fields."""
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.crawl4ai_engine.profile_extractor import extract_professor_profile
    from ..utils.profile_merge import apply_profile_merge_to_professor

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = 1
    task.current = 0
    task.message = "正在爬取个人主页..."
    persist_task(task)

    if session_factory is None:
        session_context = get_db().session
    else:

        def session_context():
            return _session_scope(session_factory)

    try:
        with session_context() as session:
            user_settings = (
                session.query(UserSettings)
                .filter(UserSettings.user_id == task.user_id)
                .first()
            )
            from ..llm.config import resolve_llm_config

            llm_config = resolve_llm_config(user_settings, app_settings)

            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                task.status = TaskStatus.FAILED
                task.error_message = "教授不存在或无权限"
                persist_task(task)
                return

            homepage = (professor.homepage or "").strip()
            if not homepage:
                task.status = TaskStatus.FAILED
                task.error_message = "未设置个人主页 URL"
                persist_task(task)
                return

            prof_name = professor.name
            affiliation = professor.affiliation or ""

        extracted = extract_professor_profile(
            homepage,
            name=prof_name,
            affiliation=affiliation,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            model=llm_config.model,
            llm_provider=llm_config.provider,
            send_progress=lambda m: setattr(task, "message", m),
            cancel_checker=lambda: task.cancel_requested,
        )

        if task.cancel_requested:
            task.status = TaskStatus.CANCELLED
            persist_task(task)
            return

        with session_context() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                task.status = TaskStatus.FAILED
                task.error_message = "教授不存在或无权限"
                persist_task(task)
                return

            if extracted:
                apply_profile_merge_to_professor(professor, extracted)
                professor.embedding = None
            else:
                task.status = TaskStatus.FAILED
                task.error_message = "未能从个人主页提取信息"
                persist_task(task)
                return

        task.current = 1
        task.success_count = 1
        task.status = TaskStatus.COMPLETED
        task.message = f"个人主页爬取完成：{prof_name}"
        task.results.append({"success": True, "professor_id": professor_id, "name": prof_name})
        persist_task(task)
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error_message = f"个人主页爬取失败: {str(exc)}"
        task.message = "个人主页爬取失败"
        persist_task(task)


@register_task("fill-publications")
def execute_fill_publications(
    task_id: str,
    professor_id: int,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Fetch full publication details (abstracts, links) for one professor."""
    from sqlalchemy.orm.attributes import flag_modified
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..models.schema import Professor
    from ..crawler.scholar import ScholarCrawler

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在获取论文详情..."
    persist_task(task)

    if session_factory is None:
        session_context = get_db().session
    else:

        def session_context():
            return _session_scope(session_factory)

    crawler = ScholarCrawler()

    try:
        with session_context() as session:
            professor = (
                session.query(Professor)
                .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                .first()
            )
            if not professor:
                task.status = TaskStatus.FAILED
                task.error_message = "教授不存在或无权限"
                persist_task(task)
                return

            publications: list[dict] = list(professor.publications or [])
            to_fill = [
                (i, pub) for i, pub in enumerate(publications)
                if pub.get("author_pub_id") and not pub.get("abstract")
            ]
            if not to_fill:
                task.status = TaskStatus.FAILED
                task.error_message = "没有需要获取详情的论文"
                persist_task(task)
                return

            task.total = len(to_fill)

            for idx, (orig_index, pub) in enumerate(to_fill):
                if idx < task.current:
                    continue
                if task.cancel_requested:
                    break

                task.current = idx + 1
                task.message = f"正在获取论文详情 ({idx + 1}/{task.total})..."
                author_pub_id = pub["author_pub_id"]

                try:
                    details = crawler.fill_publication(author_pub_id)
                    publications[orig_index].update(details)
                    task.success_count += 1
                    task.results.append({
                        "title": pub.get("title"),
                        "success": True,
                    })
                except Exception as exc:
                    task.failed_count += 1
                    task.results.append({
                        "title": pub.get("title"),
                        "success": False,
                        "error": str(exc),
                    })

                threading.Event().wait(timeout=app_settings.request_delay)

            professor.publications = publications
            flag_modified(professor, "publications")
            professor.embedding = None

        if not task.cancel_requested:
            task.message = (
                f"论文详情获取完成：成功 {task.success_count}，失败 {task.failed_count}"
            )
        _finalize(task)
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error_message = f"获取论文详情失败: {str(exc)}"
        persist_task(task)


@register_task("batch-refresh")
def execute_batch_refresh(
    task_id: str,
    professor_ids: list[int],
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Refresh multiple professors from Google Scholar in a background task."""
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.scholar import ScholarCrawler

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = len(professor_ids)
    task.message = "正在批量更新教授..."
    persist_task(task)

    if session_factory is None:
        session_context = get_db().session
    else:

        def session_context():
            return _session_scope(session_factory)

    crawler = ScholarCrawler()
    enrichment_ids: list[int] = []

    for i, professor_id in enumerate(professor_ids):
        if i < task.current:
            continue
        if task.cancel_requested:
            break

        task.current = i + 1
        task.message = f"正在更新第 {i + 1}/{task.total} 位..."

        try:
            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if not professor or not professor.google_scholar_id:
                    task.failed_count += 1
                    task.results.append({
                        "professor_id": professor_id,
                        "success": False,
                        "error": "教授不存在或缺少 Google Scholar ID",
                    })
                    continue

                scholar_id = professor.google_scholar_id
                prof_name = professor.name

            author_data = crawler.get_author(scholar_id)

            if not author_data:
                task.failed_count += 1
                task.results.append({
                    "professor_id": professor_id,
                    "name": prof_name,
                    "success": False,
                    "error": "未找到学者信息",
                })
                continue

            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if professor:
                    from .source_input_service import keep_non_scholar_paper_summaries
                    from ..utils.name_locales import apply_scholar_name_update
                    from ..utils.publication_merge import merge_publications

                    professor.paper_summaries = keep_non_scholar_paper_summaries(
                        professor.paper_summaries or []
                    )
                    from ..utils.profile_merge import apply_external_affiliation

                    apply_scholar_name_update(professor, author_data.get("name"))
                    apply_external_affiliation(professor, author_data.get("affiliation"))
                    professor.email = author_data.get("email") or professor.email
                    professor.homepage = author_data.get("homepage") or professor.homepage
                    professor.research_interests = author_data.get("interests", [])
                    professor.publications = merge_publications(
                        professor.publications,
                        author_data.get("publications", []),
                        "scholar",
                    )
                    professor.h_index = author_data.get("h_index")
                    professor.total_citations = author_data.get("citations")
                    professor.embedding = None

            task.success_count += 1
            task.results.append({
                "professor_id": professor_id,
                "name": prof_name,
                "success": True,
            })
            enrichment_ids.append(professor_id)

        except Exception as exc:
            task.failed_count += 1
            task.results.append({
                "professor_id": professor_id,
                "success": False,
                "error": str(exc),
            })

    if task.cancel_requested:
        _finalize(task)
        return
    if task.success_count == 0 and task.failed_count > 0:
        task.status = TaskStatus.FAILED
        task.error_message = "批量更新失败，请检查任务详情后重试"
        task.message = f"批量更新失败：成功 {task.success_count}，失败 {task.failed_count}"
        persist_task(task)
        return

    task.message = f"批量更新完成：成功 {task.success_count}，失败 {task.failed_count}"
    _finalize(task)
    if enrichment_ids and task.status == TaskStatus.COMPLETED:
        with get_db().session() as session:
            row = (
                session.query(UserSettings)
                .filter(UserSettings.user_id == task.user_id)
                .first()
            )
            enrich_flags = flags_from_user_settings_row(row)
        if any_auto_enrich_substep_enabled(enrich_flags):
            batch_enrich = create_task(
                "batch-professor-enrichment",
                f"教授信息增强 ({len(enrichment_ids)} 位)",
                task.user_id,
                total=len(enrichment_ids),
                parent_task_id=task.task_id,
            )
            enqueue_task(
                "batch-professor-enrichment",
                batch_enrich.task_id,
                professor_ids=enrichment_ids,
            )


@register_task("batch-refresh-dblp")
def execute_batch_refresh_dblp(
    task_id: str,
    professor_ids: list[int],
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Refresh DBLP publications for multiple professors."""
    from ..db.database import get_db
    from ..models.schema import Professor, UserSettings
    from ..crawler.dblp import DblpClient
    from ..utils.publication_merge import merge_publications
    from .source_input_service import keep_paper_summaries_excluding

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = len(professor_ids)
    task.message = "正在批量更新 DBLP..."
    persist_task(task)

    if session_factory is None:
        session_context = get_db().session
    else:

        def session_context():
            return _session_scope(session_factory)

    client = DblpClient()
    enrichment_ids: list[int] = []

    for i, professor_id in enumerate(professor_ids):
        if i < task.current:
            continue
        if task.cancel_requested:
            break
        task.current = i + 1
        try:
            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if not professor or not professor.dblp_pid:
                    task.failed_count += 1
                    continue
                pid = professor.dblp_pid
                prof_name = professor.name

            author_data = client.get_author(pid)
            if not author_data:
                task.failed_count += 1
                continue

            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if professor:
                    from ..utils.name_locales import apply_dblp_name_update
                    from ..utils.profile_merge import apply_external_affiliation

                    apply_external_affiliation(professor, author_data.get("affiliation"))
                    professor.publications = merge_publications(
                        professor.publications,
                        author_data.get("publications", []),
                        "dblp",
                    )
                    professor.paper_summaries = keep_paper_summaries_excluding(
                        professor.paper_summaries or [], {"dblp_pub"}
                    )
                    professor.dblp_url = author_data.get("dblp_url") or professor.dblp_url
                    apply_dblp_name_update(professor, author_data.get("name"))
                    professor.embedding = None

            task.success_count += 1
            task.results.append({"professor_id": professor_id, "name": prof_name, "success": True})
            enrichment_ids.append(professor_id)
        except Exception as exc:
            task.failed_count += 1
            task.results.append({"professor_id": professor_id, "success": False, "error": str(exc)})

    if not task.cancel_requested:
        task.message = f"DBLP 批量更新完成：成功 {task.success_count}，失败 {task.failed_count}"
    _finalize(task)
    if enrichment_ids and task.status == TaskStatus.COMPLETED:
        _enqueue_batch_professor_enrichment_if_enabled(
            task.user_id, enrichment_ids, parent_task_id=task.task_id
        )


@register_task("batch-refresh-external")
def execute_batch_refresh_external(
    task_id: str,
    professor_ids: list[int],
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Refresh Scholar and/or DBLP per professor."""
    from ..db.database import get_db
    from ..models.schema import Professor
    from ..crawler.scholar import ScholarCrawler
    from ..crawler.dblp import DblpClient
    from ..utils.publication_merge import merge_publications
    from .source_input_service import (
        keep_non_scholar_paper_summaries,
        keep_paper_summaries_excluding,
    )

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = len(professor_ids)
    persist_task(task)

    if session_factory is None:
        session_context = get_db().session
    else:

        def session_context():
            return _session_scope(session_factory)

    scholar = ScholarCrawler()
    dblp = DblpClient()
    enrichment_ids: list[int] = []

    for i, professor_id in enumerate(professor_ids):
        if i < task.current:
            continue
        if task.cancel_requested:
            break
        task.current = i + 1
        task.message = f"正在更新外部档案 {i + 1}/{task.total}..."
        try:
            with session_context() as session:
                professor = (
                    session.query(Professor)
                    .filter(Professor.id == professor_id, Professor.user_id == task.user_id)
                    .first()
                )
                if not professor:
                    task.failed_count += 1
                    continue
                scholar_id = professor.google_scholar_id
                dblp_pid = professor.dblp_pid
                prof_name = professor.name

            updated = False
            if scholar_id:
                author_data = scholar.get_author(scholar_id)
                if author_data:
                    with session_context() as session:
                        professor = (
                            session.query(Professor)
                            .filter(
                                Professor.id == professor_id,
                                Professor.user_id == task.user_id,
                            )
                            .first()
                        )
                        if professor:
                            professor.paper_summaries = keep_non_scholar_paper_summaries(
                                professor.paper_summaries or []
                            )
                            professor.publications = merge_publications(
                                professor.publications,
                                author_data.get("publications", []),
                                "scholar",
                            )
                            professor.h_index = author_data.get("h_index")
                            professor.total_citations = author_data.get("citations")
                            professor.research_interests = author_data.get("interests", [])
                            updated = True

            if dblp_pid:
                dblp_data = dblp.get_author(dblp_pid)
                if dblp_data:
                    with session_context() as session:
                        professor = (
                            session.query(Professor)
                            .filter(
                                Professor.id == professor_id,
                                Professor.user_id == task.user_id,
                            )
                            .first()
                        )
                        if professor:
                            professor.publications = merge_publications(
                                professor.publications,
                                dblp_data.get("publications", []),
                                "dblp",
                            )
                            professor.paper_summaries = keep_paper_summaries_excluding(
                                professor.paper_summaries or [], {"dblp_pub"}
                            )
                            updated = True

            if updated:
                with session_context() as session:
                    professor = (
                        session.query(Professor)
                        .filter(
                            Professor.id == professor_id,
                            Professor.user_id == task.user_id,
                        )
                        .first()
                    )
                    if professor:
                        professor.embedding = None
                task.success_count += 1
                enrichment_ids.append(professor_id)
            else:
                task.failed_count += 1
        except Exception as exc:
            task.failed_count += 1
            task.results.append({"professor_id": professor_id, "error": str(exc)})

    if not task.cancel_requested:
        task.message = f"外部档案更新完成：成功 {task.success_count}，失败 {task.failed_count}"
    _finalize(task)
    if enrichment_ids and task.status == TaskStatus.COMPLETED:
        _enqueue_batch_professor_enrichment_if_enabled(
            task.user_id, enrichment_ids, parent_task_id=task.task_id
        )


@register_task("profile-refine")
def execute_profile_chat_refinement(
    task_id: str,
    *,
    profile_id: int,
    chat_history: list[dict],
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Regenerate an academic profile incorporating chat Q&A insights."""
    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..ai_workflows.provider import LLMProvider
    from ..ai_workflows.workflows import refine_profile_from_chat
    from ..models.schema import UserProfile, UserSettings

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.total = 4
    task.current = 0
    task.message = "正在整理对话内容..."
    persist_task(task)

    try:
        task.message = "正在调用 AI 分析..."
        task.current = 1
        persist_task(task)

        if session_factory is None:
            session_context = get_db().session
        else:

            def session_context():
                return _session_scope(session_factory)

        with session_context() as session:
            user_settings = (
                session.query(UserSettings)
                .filter(UserSettings.user_id == task.user_id)
                .first()
            )
            provider = _llm_provider_for_user_settings_row(user_settings)

            profile = (
                session.query(UserProfile)
                .filter(UserProfile.id == profile_id, UserProfile.user_id == task.user_id)
                .first()
            )
            if not profile:
                raise ValueError("画像不存在")

            materials = profile.profile_materials or []
            manual_inputs = profile.manual_inputs or {}
            academic_profile = profile.academic_profile or ""
            profile_analysis = profile.profile_analysis or {}

            if (
                not any(
                    m.get("content") for m in materials if m.get("source_type") == "file"
                )
                and profile.raw_content
            ):
                file_materials = [
                    {"source_type": "file", "filename": "原始材料汇总", "content": profile.raw_content}
                ]
                manual_materials = [m for m in materials if m.get("source_type") == "manual"]
                materials = file_materials + manual_materials

            if profile.experience_pool_id:
                from .experience_pool_service import format_pool_stories_material

                pool_material = format_pool_stories_material(
                    session, profile.experience_pool_id, language="zh"
                )
                if pool_material is not None:
                    materials = [
                        m
                        for m in materials
                        if m.get("source_type") != "experience_pool"
                    ] + [pool_material]

        task.current = 2
        task.message = "正在重新生成学生画像..."
        persist_task(task)

        if task.cancel_requested:
            raise TaskCancelled()

        profile_result = refine_profile_from_chat(
            materials=materials,
            manual_inputs=manual_inputs,
            chat_history=chat_history,
            academic_profile=academic_profile,
            profile_analysis=profile_analysis,
            language="en",
            provider=provider,
        )

        task.current = 3
        task.message = "正在保存优化结果..."
        persist_task(task)

        if task.cancel_requested:
            raise TaskCancelled()

        with session_context() as session:
            profile = (
                session.query(UserProfile)
                .filter(UserProfile.id == profile_id, UserProfile.user_id == task.user_id)
                .first()
            )
            if profile:
                profile.academic_profile = profile_result.academic_profile
                profile.profile_analysis = profile_result.profile_analysis
                profile.evidence_notes = profile_result.evidence_notes
                profile.conflict_notes = profile_result.conflict_notes
                profile.profile_generated_at = datetime.now(timezone.utc)
                session.flush()

        task.current = 4
        task.success_count = 1
        task.status = TaskStatus.COMPLETED
        task.message = "学生画像优化完成"
        persist_task(task)

    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        task.message = "学生画像优化已取消"
        persist_task(task)
    except ValueError as exc:
        task.status = TaskStatus.FAILED
        task.error_message = str(exc)
        task.message = f"画像优化失败：{exc}"
        persist_task(task)
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error_message = str(exc)
        task.message = "画像优化过程中发生未知错误"
        persist_task(task)


@register_task("download-model")
def execute_download_model(task_id: str) -> None:
    """Download the Qwen3-Embedding-0.6B model from ModelScope."""
    from ..matcher.semantic_matcher import _get_model

    task = get_task(task_id)
    if not task:
        return
    task.status = TaskStatus.RUNNING
    task.message = "正在从 ModelScope 下载模型，预计 3-5 分钟..."
    persist_task(task)

    class _DownloadProgress:
        """ProgressCallback that forwards model.safetensors progress to the task state."""

        def __init__(self, filename: str, file_size: int):
            self.filename = filename
            self.file_size = file_size
            self.downloaded = 0
            self._last_pct = -1

        def update(self, size: int):
            if task.cancel_requested:
                raise TaskCancelled()
            if "model.safetensors" not in self.filename or self.file_size <= 0:
                return
            self.downloaded += size
            pct = int(self.downloaded / self.file_size * 100)
            pct = min(pct, 100)
            if pct == self._last_pct:
                return
            self._last_pct = pct
            task.current = pct
            task.message = f"正在下载模型... {pct}%"
            persist_task(task)

        def end(self):
            pass

    try:
        if task.cancel_requested:
            raise TaskCancelled()
        _get_model(progress_callbacks=[_DownloadProgress])
        task.current = 100
        task.status = TaskStatus.COMPLETED
        task.message = "模型下载完成"
        persist_task(task)
    except TaskCancelled:
        task.status = TaskStatus.CANCELLED
        task.message = "模型下载已取消"
        persist_task(task)
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error_message = f"模型下载失败: {exc}"
        persist_task(task)
