"""Background task state management and execution coroutines."""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs


class TaskStatus(str, Enum):
    """Task lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class TaskState:
    """State of a background task."""

    task_id: str
    task_type: str  # batch-crawl | batch-letters | single-crawl | match | single-letter
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# In-memory task registry (lost on server restart — acceptable for personal use)
_tasks: Dict[str, TaskState] = {}


# ---------------------------------------------------------------------------
# Task registry helpers
# ---------------------------------------------------------------------------


def create_task(task_type: str, task_name: str, user_id: int, total: int) -> TaskState:
    """Create and register a new task."""
    task_id = str(uuid.uuid4())
    task = TaskState(
        task_id=task_id,
        task_type=task_type,
        task_name=task_name,
        user_id=user_id,
        status=TaskStatus.PENDING,
        total=total,
    )
    _tasks[task_id] = task
    return task


def get_task(task_id: str) -> Optional[TaskState]:
    """Look up a task by ID."""
    return _tasks.get(task_id)


def get_user_tasks(user_id: int) -> List[TaskState]:
    """Return PENDING / RUNNING / FAILED tasks for a user (for UI recovery)."""
    return [
        t for t in _tasks.values()
        if t.user_id == user_id
        and t.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.FAILED)
    ]


def cleanup_old_tasks() -> None:
    """Remove completed / cancelled tasks older than 5 minutes."""
    now = datetime.now(timezone.utc)
    stale = [
        tid for tid, t in _tasks.items()
        if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED)
        and (now - t.created_at).total_seconds() > 300
    ]
    for tid in stale:
        del _tasks[tid]


# ---------------------------------------------------------------------------
# URL utility (shared by executor and professor route)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Background execution coroutines
# ---------------------------------------------------------------------------


async def execute_batch_crawl(task: TaskState, scholar_urls: List[str]) -> None:
    """Crawl a list of Google Scholar URLs and persist each author."""
    from ..db.database import get_db
    from ..models.schema import Professor
    from ..crawler.scholar import ScholarCrawler

    task.status = TaskStatus.RUNNING
    db = get_db()
    crawler = ScholarCrawler()

    for i, url in enumerate(scholar_urls):
        if task.cancel_requested:
            break

        task.current = i + 1
        task.message = f"正在爬取第 {i + 1}/{task.total} 个..."

        try:
            scholar_id = extract_scholar_id_from_url(url)
            # Blocking network call — run in thread pool to avoid blocking event loop
            author_data = await asyncio.to_thread(crawler.get_author, scholar_id)

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
                        session.add(professor)

                task.success_count += 1
                task.results.append({"url": url, "name": author_data["name"], "success": True})
            else:
                task.failed_count += 1
                task.results.append({"url": url, "success": False, "error": "未找到学者信息"})

        except Exception as e:
            task.failed_count += 1
            task.results.append({"url": url, "success": False, "error": str(e)})

        await asyncio.sleep(0)  # yield to event loop

    task.status = TaskStatus.CANCELLED if task.cancel_requested else TaskStatus.COMPLETED


async def execute_batch_letters(
    task: TaskState,
    professor_ids: List[int],
    profile_id: int,
    api_key: str,
) -> None:
    """Generate contact letters for a list of professors."""
    from datetime import datetime, timezone
    from ..db.database import get_db
    from ..models.schema import MatchRecord, Professor, UserProfile
    from ..llm.letter_generator import LetterGenerator

    task.status = TaskStatus.RUNNING
    db = get_db()
    generator = LetterGenerator(api_key=api_key)

    for i, professor_id in enumerate(professor_ids):
        if task.cancel_requested:
            break

        task.current = i + 1

        try:
            # Read phase — get match record, professor, and profile
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

                profile_data = {
                    "name": profile.name,
                    "education": profile.education or [],
                    "research_experience": profile.research_experience or [],
                    "projects": profile.projects or [],
                    "skills": profile.skills or [],
                }
                prof_data = {
                    "name": professor.name,
                    "affiliation": professor.affiliation,
                    "research_interests": professor.research_interests or [],
                    "publications": professor.publications or [],
                }
                reasons = match_record.match_reasons or []

            # LLM call — blocking, run in thread pool
            letter_content = await asyncio.to_thread(
                generator.generate,
                profile=profile_data,
                professor=prof_data,
                match_reasons=reasons,
            )

            # Write phase — save generated letter
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
            task.failed_count += 1
            task.results.append({"professor_id": professor_id, "success": False, "error": str(e)})

        await asyncio.sleep(0)  # yield to event loop

    task.status = TaskStatus.CANCELLED if task.cancel_requested else TaskStatus.COMPLETED


async def execute_single_crawl(task: TaskState, scholar_url: str) -> None:
    """Crawl a single Google Scholar profile and persist the professor."""
    from ..db.database import get_db
    from ..models.schema import Professor
    from ..crawler.scholar import ScholarCrawler

    task.status = TaskStatus.RUNNING
    task.message = "正在爬取教授信息..."
    db = get_db()

    try:
        scholar_id = extract_scholar_id_from_url(scholar_url)
        crawler = ScholarCrawler()
        author_data = await asyncio.to_thread(crawler.get_author, scholar_id)

        if not author_data:
            task.status = TaskStatus.FAILED
            task.error_message = "未找到该学者信息"
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
            if existing:
                task.status = TaskStatus.FAILED
                task.error_message = "该教授已存在"
                return

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
            )
            session.add(professor)

        task.success_count = 1
        task.current = 1
        task.results.append({"name": author_data["name"], "success": True})
        task.status = TaskStatus.COMPLETED

    except ValueError as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"爬取失败: {str(e)}"


async def execute_match(task: TaskState, profile_id: int) -> None:
    """Run the keyword matching algorithm against all professors."""
    from ..db.database import get_db
    from ..models.schema import UserProfile, Professor, MatchRecord
    from ..matcher.keyword_matcher import KeywordMatcher

    task.status = TaskStatus.RUNNING
    task.message = "正在运行匹配算法..."
    db = get_db()

    try:
        with db.session() as session:
            active_profile = session.query(UserProfile).filter(
                UserProfile.id == profile_id
            ).first()
            if not active_profile:
                task.status = TaskStatus.FAILED
                task.error_message = "简历不存在"
                return

            professors = (
                session.query(Professor)
                .filter(Professor.user_id == task.user_id)
                .all()
            )
            if not professors:
                task.status = TaskStatus.FAILED
                task.error_message = "请先添加教授"
                return

            # Clear existing match records for this profile
            session.query(MatchRecord).filter(
                MatchRecord.user_profile_id == profile_id
            ).delete(synchronize_session=False)

            matcher = KeywordMatcher()
            profile_data = {
                "name": active_profile.name,
                "education": active_profile.education or [],
                "research_experience": active_profile.research_experience or [],
                "projects": active_profile.projects or [],
                "skills": active_profile.skills or [],
            }

            for i, professor in enumerate(professors):
                if task.cancel_requested:
                    break

                task.current = i + 1
                task.message = f"正在匹配 {professor.name}..."

                prof_data = {
                    "name": professor.name,
                    "affiliation": professor.affiliation,
                    "research_interests": professor.research_interests or [],
                    "publications": professor.publications or [],
                }
                score, reasons = matcher.match(profile_data, prof_data)
                session.add(
                    MatchRecord(
                        user_profile_id=profile_id,
                        professor_id=professor.id,
                        score=score,
                        match_reasons=reasons,
                    )
                )
                task.success_count += 1

        task.status = TaskStatus.CANCELLED if task.cancel_requested else TaskStatus.COMPLETED
        if task.status == TaskStatus.COMPLETED:
            task.message = f"匹配完成，共 {task.success_count} 位教授"

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"匹配失败: {str(e)}"


async def execute_single_letter(
    task: TaskState,
    professor_id: int,
    profile_id: int,
    api_key: str,
) -> None:
    """Generate a contact letter for one professor."""
    from datetime import datetime, timezone
    from ..db.database import get_db
    from ..models.schema import MatchRecord, Professor, UserProfile
    from ..llm.letter_generator import LetterGenerator

    task.status = TaskStatus.RUNNING
    db = get_db()

    try:
        # Read phase
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
                task.status = TaskStatus.FAILED
                task.error_message = "未找到匹配记录，请先运行匹配"
                return

            match_record, professor, profile = result
            task.message = f"正在为 {professor.name} 生成邮件..."

            profile_data = {
                "name": profile.name,
                "education": profile.education or [],
                "research_experience": profile.research_experience or [],
                "projects": profile.projects or [],
                "skills": profile.skills or [],
            }
            prof_data = {
                "name": professor.name,
                "affiliation": professor.affiliation,
                "research_interests": professor.research_interests or [],
                "publications": professor.publications or [],
            }
            reasons = match_record.match_reasons or []

        # LLM call — blocking, run in thread pool
        generator = LetterGenerator(api_key=api_key)
        letter_content = await asyncio.to_thread(
            generator.generate,
            profile=profile_data,
            professor=prof_data,
            match_reasons=reasons,
        )

        # Write phase
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
        task.status = TaskStatus.COMPLETED

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"生成失败: {str(e)}"
