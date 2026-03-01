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
    task_type: str  # batch-crawl | batch-letters | single-crawl | match | single-letter | paper-summary
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


def _run_encoding_in_thread(
    professor_texts: list[str],
    profile_text: str,
) -> tuple[list[list[float]], list[float]]:
    """Run model load + encode in a worker thread to avoid blocking the event loop.

    Returns (professor_embeddings, profile_embedding).
    """
    from ..matcher.semantic_matcher import encode_texts

    prof_vecs = []
    if professor_texts:
        vecs = encode_texts(professor_texts)
        prof_vecs = [v.tolist() for v in vecs]
    profile_vec = encode_texts([profile_text])[0].tolist()
    return prof_vecs, profile_vec


async def execute_match(task: TaskState, profile_id: int) -> None:
    """Run semantic matching against all professors using allenai-specter embeddings.

    Model loading and encoding run in a thread pool so the event loop stays responsive
    (SSE, task list, other requests work while model downloads/encodes).
    """
    from ..db.database import get_db
    from ..models.schema import UserProfile, Professor, MatchRecord
    from ..matcher.semantic_matcher import (
        SemanticMatcher,
        build_professor_text,
        build_profile_text,
    )

    task.status = TaskStatus.RUNNING
    task.message = "正在加载语义匹配模型..."
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

            # Reset scores/reasons for this profile but keep generated letters.
            # Deleting records would destroy letter_content stored on MatchRecord.
            existing_records: dict[int, MatchRecord] = {
                r.professor_id: r
                for r in session.query(MatchRecord).filter(
                    MatchRecord.user_profile_id == profile_id
                ).all()
            }

            profile_data = {
                "name": active_profile.name,
                "education": active_profile.education or [],
                "research_experience": active_profile.research_experience or [],
                "projects": active_profile.projects or [],
                "skills": active_profile.skills or [],
            }

            # Prepare texts for encoding (no model access yet).
            missing = [p for p in professors if not p.embedding]
            professor_texts = [
                build_professor_text({
                    "research_interests": p.research_interests or [],
                    "publications": p.publications or [],
                    "paper_summaries": p.paper_summaries or [],
                    "affiliation": p.affiliation or "",
                })
                for p in missing
            ]
            profile_text = build_profile_text(profile_data)

            # Run model load + encode in a thread so event loop stays responsive.
            task.message = "正在计算语义向量（首次可能需下载模型）..."
            prof_vecs, profile_vec = await asyncio.to_thread(
                _run_encoding_in_thread, professor_texts, profile_text
            )

            # Persist professor embeddings in main thread (DB).
            for prof, vec in zip(missing, prof_vecs):
                prof.embedding = vec
            if missing:
                session.flush()

            matcher = SemanticMatcher()
            task.message = "正在语义匹配..."

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
                    "paper_summaries": professor.paper_summaries or [],
                }
                score, reasons = matcher.match(
                    profile_data,
                    prof_data,
                    professor_embedding=professor.embedding,
                    profile_embedding=profile_vec,
                )
                existing = existing_records.get(professor.id)
                if existing:
                    # Update score/reasons in place; letter_content is preserved.
                    existing.score = score
                    existing.match_reasons = reasons
                else:
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


async def execute_university_crawl(task: TaskState, university_id: str) -> None:
    """Crawl all professors from a registered university department website.

    Runs the university-specific crawler in a thread pool (blocking network I/O),
    then persists each professor to the database, skipping duplicates.

    Args:
        task: The background task state object (mutated in place).
        university_id: Key into the university crawler registry (e.g. "xjtu-cs").
    """
    from ..db.database import get_db
    from ..models.schema import Professor
    from ..crawler.universities.registry import get_crawler

    task.status = TaskStatus.RUNNING
    task.message = "正在初始化爬虫..."
    db = get_db()

    try:
        crawler = get_crawler(university_id)
    except KeyError:
        task.status = TaskStatus.FAILED
        task.error_message = f"未找到院校爬虫: {university_id}"
        return

    task.message = f"正在爬取 {crawler.display_name}..."

    try:
        # Blocking network I/O — run in thread pool
        professors_data: list[dict] = await asyncio.to_thread(crawler.crawl_all)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = f"爬取失败: {str(e)}"
        return

    total = len(professors_data)
    task.total = total
    task.message = f"共获取 {total} 条记录，正在入库..."

    for i, prof_data in enumerate(professors_data):
        if task.cancel_requested:
            break

        task.current = i + 1
        task.message = f"正在保存第 {i + 1}/{total} 位: {prof_data.get('name', '')}"

        try:
            with db.session() as session:
                # Deduplicate by (user_id, name, affiliation)
                existing = (
                    session.query(Professor)
                    .filter(
                        Professor.user_id == task.user_id,
                        Professor.name == prof_data["name"],
                        Professor.affiliation == prof_data.get("affiliation"),
                    )
                    .first()
                )
                if existing:
                    task.results.append(
                        {"name": prof_data["name"], "success": True, "skipped": True}
                    )
                    continue

                professor = Professor(
                    user_id=task.user_id,
                    name=prof_data["name"],
                    affiliation=prof_data.get("affiliation"),
                    email=prof_data.get("email"),
                    homepage=prof_data.get("homepage"),
                    research_interests=prof_data.get("research_interests", []),
                    publications=[],
                )
                session.add(professor)

            task.success_count += 1
            task.results.append({"name": prof_data["name"], "success": True, "skipped": False})

        except Exception as e:
            task.failed_count += 1
            task.results.append({"name": prof_data.get("name", "?"), "success": False, "error": str(e)})

        await asyncio.sleep(0)  # yield to event loop

    task.status = TaskStatus.CANCELLED if task.cancel_requested else TaskStatus.COMPLETED
    if task.status == TaskStatus.COMPLETED:
        skipped = sum(1 for r in task.results if r.get("skipped"))
        task.message = (
            f"完成！新增 {task.success_count} 位，跳过重复 {skipped} 位，失败 {task.failed_count} 位"
        )


async def execute_professor_source_summary(
    task: TaskState,
    professor_id: int,
    source_input_ids: list[int],
) -> None:
    """Summarize selected source inputs and persist paper summaries."""
    from sqlalchemy.orm.attributes import flag_modified

    from ..config import settings as app_settings
    from ..db.database import get_db
    from ..llm import PaperSummarizer
    from ..models.schema import Professor, SourceInput, UserSettings
    from .source_input_service import build_paper_summary_from_source

    task.status = TaskStatus.RUNNING
    task.message = "正在准备论文总结任务..."
    db = get_db()

    if not source_input_ids:
        task.status = TaskStatus.FAILED
        task.error_message = "请先选择需要总结的来源输入"
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
            return

        user_settings = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == task.user_id)
            .first()
        )
        api_key = (user_settings.deepseek_api_key if user_settings else None) or app_settings.deepseek_api_key
        base_url = (user_settings.deepseek_base_url if user_settings else None) or app_settings.deepseek_base_url
    summarizer = PaperSummarizer(api_key=api_key, base_url=base_url)

    for idx, source_id in enumerate(source_input_ids, start=1):
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
                    task.results.append({"source_input_id": source_id, "success": False, "error": "来源输入不存在"})
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
                    summarizer=summarizer,
                )
                if not summary:
                    task.failed_count += 1
                    task.results.append({"source_input_id": source_id, "success": False, "error": "无法生成论文总结"})
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

        await asyncio.sleep(0)

    if task.cancel_requested:
        task.status = TaskStatus.CANCELLED
        return
    if task.success_count == 0 and task.failed_count > 0:
        task.status = TaskStatus.FAILED
        task.error_message = "论文总结失败，请检查任务详情后重试"
        task.message = f"论文总结失败：成功 {task.success_count}，失败 {task.failed_count}"
        return

    task.status = TaskStatus.COMPLETED
    task.message = f"论文总结完成：成功 {task.success_count}，失败 {task.failed_count}"
