"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..db.database import get_db
from ..runtime import frontend_dist_dir, is_configured, is_packaged
from .bootstrap import init_admin_user
from .routes.auth import router as auth_router, admin_router
from .routes.setup import router as setup_router
from .routes.profiles import router as profiles_router
from .routes.professors import router as professors_router
from .routes.match import router as match_router
from .routes.letters import router as letters_router
from .routes.settings import router as settings_router
from .routes.tasks import router as tasks_router
from .routes.source_inputs import router as source_inputs_router
from .task_queue import start_consumer, stop_consumer, enqueue_task
from .task_manager import (
    TaskStatus,
    TaskState,
    _tasks,
    _tasks_lock,
    persist_task,
    cleanup_old_tasks,
)


def _rehydrate_tasks():
    """Load PENDING/RUNNING tasks from DB into in-memory dict on startup."""
    from ..models.background_task import BackgroundTask

    db = get_db()
    rehydrated = 0
    with db.session() as session:
        pending = (
            session.query(BackgroundTask)
            .filter(BackgroundTask.status.in_(["pending", "running"]))
            .all()
        )
        for row in pending:
            task = TaskState(
                task_id=row.task_id,
                task_type=row.task_type,
                task_name=row.task_name,
                user_id=row.user_id,
                status=TaskStatus.PENDING,
                total=row.total,
                current=0,
                success_count=row.success_count,
                failed_count=row.failed_count,
                message=row.message,
                error_message=row.error_message,
                results=row.results or [],
                cancel_requested=row.cancel_requested,
                created_at=row.created_at,
                enqueue_args=row.enqueue_args or [],
                enqueue_kwargs=row.enqueue_kwargs or {},
            )
            with _tasks_lock:
                _tasks[task.task_id] = task

            if task.cancel_requested:
                row.status = "cancelled"
                task.status = TaskStatus.CANCELLED
                task.message = task.message or "任务已取消"
                persist_task(task)
                continue

            # Only re-enqueue tasks that have stored arguments from the
            # Huey-powered system.  Tasks created before the migration have
            # no enqueue_args and cannot be replayed — mark them failed.
            if task.enqueue_args or task.enqueue_kwargs:
                row.status = "pending"
                persist_task(task)
                enqueue_task(
                    task.task_type, task.task_id,
                    *task.enqueue_args, **task.enqueue_kwargs,
                )
                rehydrated += 1
            else:
                row.status = "failed"
                task.status = TaskStatus.FAILED
                task.error_message = "任务缺少重放参数（迁移前的旧任务），无法恢复"
                persist_task(task)

    if rehydrated:
        print(f"已在数据库中恢复 {rehydrated} 个未完成的任务")


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
                    content={
                        "detail": "请先完成首次存储路径配置",
                    },
                )
        return await call_next(request)

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
    
    @app.get("/api/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "message": "Prof-Finder API is running"}

    _configure_frontend_static(app)
    
    return app


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
            raise HTTPException(status_code=404, detail="Not Found")

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
