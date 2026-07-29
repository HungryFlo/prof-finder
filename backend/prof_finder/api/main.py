"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..db.database import get_db
from ..runtime import frontend_dist_dir, is_configured, is_packaged
from .bootstrap import init_admin_user
from .errors import (
    ApiError,
    ErrorCode,
    error_body,
    format_validation_errors,
)
from .routes.auth import router as auth_router, admin_router
from .routes.setup import router as setup_router
from .routes.profiles import router as profiles_router
from .routes.professors import router as professors_router
from .routes.match import router as match_router
from .routes.letters import router as letters_router
from .routes.settings import router as settings_router
from .routes.tasks import router as tasks_router
from .routes.source_inputs import router as source_inputs_router
from .routes.universities import router as universities_router
from .task_queue import start_consumer, stop_consumer, enqueue_task, flush_queue
from .task_manager import (
    TaskStatus,
    TaskState,
    _tasks,
    _tasks_lock,
    persist_task,
    cleanup_old_tasks,
)


def _rehydrate_tasks():
    """Reconcile task state from the DB on startup after a (possibly
    ungraceful) shutdown.

    The ``background_tasks`` table is the single source of truth; anything
    still sitting in Huey's own persistent queue or in memory from before
    this process started is untrustworthy and must be discarded/recomputed
    from it. Three cases, decided per row that was PENDING/RUNNING when the
    process went away:

    1. ``cancel_requested`` is set — the user's cancel intent is durable
       (it was fsync'd to SQLite before the cancel endpoint responded), so
       we honor it unconditionally and finalize as CANCELLED. This also
       cascades to any child tasks spawned by this task.
    2. Status was PENDING (never actually started executing) — safe to
       simply re-enqueue with the original arguments; no partial work could
       have happened.
    3. Status was RUNNING and not cancelled — the process died mid-flight.
       We do NOT silently re-run it from scratch: most executors record
       results/success_count incrementally and restarting the loop from
       index 0 would duplicate every already-recorded item. Instead we mark
       it INTERRUPTED and leave the last-persisted progress (`current`,
       `results`) untouched, surfacing it to the user so they can
       explicitly choose to resume (continue from `current`) or discard it.
    """
    from ..models.background_task import BackgroundTask

    # Discard anything left over in Huey's own persistent queue from before
    # this process started. We are about to recompute what needs to run
    # purely from `background_tasks`; any stale job left in Huey's queue
    # would otherwise be executed a second time once the consumer starts,
    # racing the freshly re-enqueued job for the same task_id.
    flush_queue()

    db = get_db()
    rehydrated = 0
    interrupted = 0
    with db.session() as session:
        pending = (
            session.query(BackgroundTask)
            .filter(BackgroundTask.status.in_(["pending", "running"]))
            .all()
        )
        # Cancel intent cascades to children: pre-compute which tasks are
        # (transitively) cancelled so a child whose parent was cancelled is
        # cancelled too, even if the child itself was never asked to cancel.
        rows_by_id = {row.task_id: row for row in pending}
        cancelled_ids: set[str] = set()

        def _is_cancelled(row) -> bool:
            if row.task_id in cancelled_ids:
                return True
            if row.cancel_requested:
                cancelled_ids.add(row.task_id)
                return True
            parent = rows_by_id.get(row.parent_task_id) if row.parent_task_id else None
            if parent is not None and _is_cancelled(parent):
                cancelled_ids.add(row.task_id)
                return True
            return False

        for row in pending:
            task = TaskState(
                task_id=row.task_id,
                task_type=row.task_type,
                task_name=row.task_name,
                user_id=row.user_id,
                status=TaskStatus.PENDING,
                total=row.total,
                current=row.current,
                success_count=row.success_count,
                failed_count=row.failed_count,
                message=row.message,
                error_message=row.error_message,
                results=row.results or [],
                cancel_requested=row.cancel_requested,
                created_at=row.created_at,
                enqueue_args=row.enqueue_args or [],
                enqueue_kwargs=row.enqueue_kwargs or {},
                parent_task_id=row.parent_task_id,
            )
            with _tasks_lock:
                _tasks[task.task_id] = task

            if _is_cancelled(row):
                task.cancel_requested = True
                task.status = TaskStatus.CANCELLED
                task.message = task.message or "任务已取消"
                persist_task(task)
                continue

            if row.status == "pending":
                # Never actually started — safe to replay from scratch.
                if task.enqueue_args or task.enqueue_kwargs:
                    persist_task(task)
                    enqueue_task(
                        task.task_type, task.task_id,
                        *task.enqueue_args, **task.enqueue_kwargs,
                    )
                    rehydrated += 1
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = "任务缺少重放参数（迁移前的旧任务），无法恢复"
                    persist_task(task)
                continue

            # row.status == "running": process died mid-execution without a
            # cancel request. Do not auto-resume — surface it instead.
            task.status = TaskStatus.INTERRUPTED
            task.message = "程序上次退出时该任务尚未完成，可选择继续或放弃"
            persist_task(task)
            interrupted += 1

    if rehydrated:
        print(f"已在数据库中恢复 {rehydrated} 个待执行的任务")
    if interrupted:
        print(f"检测到 {interrupted} 个因程序中断而停止的任务，等待用户处理")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    print("启动 Prof-Finder API 服务...")
    if is_configured():
        init_admin_user()
        _rehydrate_tasks()
        start_consumer()

    yield

    # Shutdown
    print("正在关闭 Prof-Finder API 服务...")
    stop_consumer()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Prof-Finder API",
        description="帮助学生寻找未来 PhD/MPhil 导师的智能匹配系统",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def require_setup_completed(request: Request, call_next):
        if is_packaged() and not is_configured():
            path = request.url.path
            if path.startswith("/api/") and not (
                path == "/api/health"
                or path.startswith("/api/setup")
            ):
                return JSONResponse(
                    status_code=403,
                    content=error_body(
                        ErrorCode.SETUP_REQUIRED,
                        "请先完成首次存储路径配置",
                    ),
                )
        return await call_next(request)

    _register_exception_handlers(app)

    # Register routers
    app.include_router(setup_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(profiles_router, prefix="/api")
    app.include_router(professors_router, prefix="/api")
    app.include_router(match_router, prefix="/api")
    app.include_router(letters_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(source_inputs_router, prefix="/api")
    app.include_router(universities_router, prefix="/api")
    
    @app.get("/api/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "message": "Prof-Finder API is running"}

    _configure_frontend_static(app)
    
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register handlers that always return ``{code, detail}``."""

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.detail),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(
                ErrorCode.VALIDATION_ERROR,
                format_validation_errors(exc.errors()),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            code = str(detail.get("code") or ErrorCode.HTTP_ERROR)
            message = str(detail.get("detail") or detail.get("message") or code)
            return JSONResponse(
                status_code=exc.status_code,
                content=error_body(code, message),
                headers=getattr(exc, "headers", None),
            )
        if isinstance(detail, str) and detail == ErrorCode.MODEL_NOT_DOWNLOADED:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_body(ErrorCode.MODEL_NOT_DOWNLOADED, detail),
                headers=getattr(exc, "headers", None),
            )
        message = detail if isinstance(detail, str) else str(detail)
        code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.HTTP_ERROR
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, message),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_body(ErrorCode.INTERNAL_ERROR, str(exc) or "Internal server error"),
        )


def _configure_frontend_static(app: FastAPI) -> None:
    """Serve the built Vue app when frontend assets are available."""
    dist_dir = frontend_dist_dir()
    if dist_dir is None:
        return

    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    dist_root = dist_dir.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Return static files or the SPA entry point for browser routes."""
        if full_path == "api" or full_path.startswith("api/"):
            raise ApiError(404, ErrorCode.NOT_FOUND, "Not Found")

        requested = (dist_root / full_path).resolve()
        if requested.is_file() and _is_relative_to(requested, dist_root):
            return FileResponse(requested)
        return FileResponse(dist_root / "index.html")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


# Create the app instance
app = create_app()
