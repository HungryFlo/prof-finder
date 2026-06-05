"""Async task API routes with SSE progress streaming."""

import asyncio
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from ...models.schema import User, UserProfile, UserSettings
from ...config import settings as app_settings
from ...utils.query_cache import get_active_profile
from ..deps import get_db_session, get_current_user
from ..deps import get_current_user_sse
from ..schemas import (
    TaskStartResponse,
    TaskCancelResponse,
    TaskListItemResponse,
    BatchCrawlRequest,
    BatchDblpCrawlRequest,
    BatchLetterRequest,
)
from ..task_manager import (
    TaskStatus,
    TaskState,
    create_task,
    get_task,
    get_user_tasks,
    cleanup_old_tasks,
    enqueue_task,
    persist_task,
)
from ..task_queue import huey

router = APIRouter(prefix="/tasks", tags=["异步任务"])


# ---------------------------------------------------------------------------
# Batch task endpoints
# ---------------------------------------------------------------------------


@router.post("/batch-crawl", response_model=TaskStartResponse)
async def start_batch_crawl(
    data: BatchCrawlRequest,
    current_user: User = Depends(get_current_user),
):
    """Start a batch professor crawl task.

    Args:
        data: List of Google Scholar URLs.
        current_user: Authenticated user.

    Returns:
        Task ID for progress tracking via SSE.
    """
    if not data.scholar_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供至少一个 Scholar URL",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-crawl",
        task_name=f"批量爬取 {len(data.scholar_urls)} 个教授",
        user_id=current_user.id,
        total=len(data.scholar_urls),
    )
    enqueue_task("batch-crawl", task.task_id, data.scholar_urls)

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动批量爬取任务，共 {len(data.scholar_urls)} 个链接",
    )


@router.post("/batch-dblp-crawl", response_model=TaskStartResponse)
async def start_batch_dblp_crawl(
    data: BatchDblpCrawlRequest,
    current_user: User = Depends(get_current_user),
):
    """Start a batch DBLP profile crawl task."""
    if not data.dblp_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供至少一个 DBLP URL",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-dblp-crawl",
        task_name=f"批量爬取 DBLP {len(data.dblp_urls)} 个教授",
        user_id=current_user.id,
        total=len(data.dblp_urls),
    )
    enqueue_task("batch-dblp-crawl", task.task_id, data.dblp_urls)

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动 DBLP 批量爬取，共 {len(data.dblp_urls)} 个链接",
    )


@router.post("/batch-letters", response_model=TaskStartResponse)
async def start_batch_letters(
    data: BatchLetterRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a batch letter generation task.

    Args:
        data: Professor IDs or top-N to generate for.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for progress tracking via SSE.
    """
    active_profile = get_active_profile(session, current_user.id)
    if not active_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先激活一份简历",
        )

    from ...llm.config import llm_not_configured_message, llm_provider_for_user_settings

    user_settings = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )
    if not llm_provider_for_user_settings(user_settings).enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=llm_not_configured_message(),
        )

    if data.professor_ids:
        professor_ids = data.professor_ids
    elif data.top:
        from ...models.schema import MatchRecord

        top_matches = (
            session.query(MatchRecord)
            .filter(MatchRecord.user_profile_id == active_profile.id)
            .order_by(MatchRecord.score.desc())
            .limit(data.top)
            .all()
        )
        professor_ids = [m.professor_id for m in top_matches]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请指定 professor_ids 或 top 参数",
        )

    if not professor_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未找到需要生成邮件的教授",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-letters",
        task_name=f"批量生成 {len(professor_ids)} 封邮件",
        user_id=current_user.id,
        total=len(professor_ids),
    )
    enqueue_task(
        "batch-letters", task.task_id, professor_ids, active_profile.id, current_user.id, data.language,
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动批量生成任务，共 {len(professor_ids)} 封邮件",
    )


# ---------------------------------------------------------------------------
# SSE progress endpoint (pure poller — task runs independently)
# ---------------------------------------------------------------------------


@router.get("/{task_id}/progress")
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(get_current_user_sse),
):
    """Stream task progress via SSE.

    Polls task state every 500ms and emits events until the task finishes.
    The task itself runs as an independent asyncio coroutine; this endpoint
    only reads state and never executes business logic.

    Args:
        task_id: Task to track.
        current_user: Authenticated user (token accepted via header or ?token= query param).

    Returns:
        SSE event stream.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务",
        )

    async def event_generator():
        # Poll until the task leaves PENDING/RUNNING
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            yield {
                "event": "progress",
                "data": json.dumps({
                    "current": task.current,
                    "total": task.total,
                    "status": task.status.value,
                    "message": task.message,
                    "cancel_requested": task.cancel_requested,
                }),
            }
            await asyncio.sleep(0.5)

        # Emit terminal event
        if task.status == TaskStatus.COMPLETED:
            yield {
                "event": "complete",
                "data": json.dumps({
                    "status": task.status.value,
                    "current": task.current,
                    "total": task.total,
                    "message": task.message,
                    "success_count": task.success_count,
                    "failed_count": task.failed_count,
                    "results": task.results,
                }),
            }
        elif task.status == TaskStatus.FAILED:
            yield {
                "event": "failed",
                "data": json.dumps({
                    "status": task.status.value,
                    "current": task.current,
                    "total": task.total,
                    "message": task.message,
                    "error_message": task.error_message,
                }),
            }
        elif task.status == TaskStatus.CANCELLED:
            yield {
                "event": "cancelled",
                "data": json.dumps({
                    "status": task.status.value,
                    "current": task.current,
                    "total": task.total,
                    "message": task.message,
                    "completed_count": task.success_count,
                }),
            }

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Cancel & list endpoints
# ---------------------------------------------------------------------------


@router.post("/{task_id}/cancel", response_model=TaskCancelResponse)
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Request cancellation of a running task.

    Args:
        task_id: Task to cancel.
        current_user: Authenticated user.

    Returns:
        Cancellation confirmation.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权取消此任务",
        )
    if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已完成或已取消",
        )

    task.cancel_requested = True

    # Also revoke from Huey queue if not yet started
    if task.huey_result_id:
        huey.revoke_by_id(task.huey_result_id)
    if task.status == TaskStatus.PENDING:
        task.status = TaskStatus.CANCELLED
        task.message = "任务已取消"
    else:
        task.message = task.message or "取消请求已发送，当前步骤完成后停止"
    persist_task(task)

    return TaskCancelResponse(
        message="取消请求已发送",
        completed_count=task.success_count,
    )


@router.get("", response_model=List[TaskListItemResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
):
    """List active (PENDING/RUNNING) and failed tasks for the current user.

    Used by the frontend to restore the task panel after a page refresh.

    Args:
        current_user: Authenticated user.

    Returns:
        List of task summaries.
    """
    tasks = get_user_tasks(current_user.id)
    return [
        TaskListItemResponse(
            task_id=t.task_id,
            task_type=t.task_type,
            task_name=t.task_name,
            status=t.status.value,
            current=t.current,
            total=t.total,
            message=t.message,
            error_message=t.error_message,
            cancel_requested=t.cancel_requested,
        )
        for t in tasks
    ]


@router.post("/{task_id}/retry", response_model=TaskStartResponse)
async def retry_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retry a failed task by creating a new task with the same parameters.

    Only tasks in FAILED status can be retried.  The new task re-uses the
    stored enqueue_args / enqueue_kwargs from the original task, ensuring
    it runs with identical parameters.

    Args:
        task_id: Failed task to retry.
        current_user: Authenticated user.

    Returns:
        New task ID for progress tracking.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权重试此任务",
        )
    if task.status != TaskStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能重试失败的任务",
        )

    # For tasks that use an API key (letter generation, profile generation),
    # re-fetch the current key from settings so that a newly-configured key
    # takes effect without requiring the user to re-trigger from the UI.
    from ...models.schema import UserSettings
    from ...config import settings as app_settings

    new_kwargs = dict(task.enqueue_kwargs)
    if "user_id" in new_kwargs:
        new_kwargs["user_id"] = current_user.id

    cleanup_old_tasks()
    new_task = create_task(
        task_type=task.task_type,
        task_name=task.task_name,
        user_id=current_user.id,
        total=task.total,
    )
    enqueue_task(
        task.task_type,
        new_task.task_id,
        *task.enqueue_args,
        **new_kwargs,
    )

    return TaskStartResponse(
        task_id=new_task.task_id,
        message="任务已重新启动",
    )
