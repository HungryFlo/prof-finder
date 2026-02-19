"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..db.database import get_db
from ..models.schema import User, UserSettings
from .auth import hash_password
from .routes.auth import router as auth_router, admin_router
from .routes.profiles import router as profiles_router
from .routes.professors import router as professors_router
from .routes.match import router as match_router
from .routes.letters import router as letters_router
from .routes.settings import router as settings_router
from .routes.tasks import router as tasks_router


def init_admin_user():
    """Initialize the admin user if it doesn't exist.
    
    Creates the admin account with credentials from settings:
    - Default: root / root123
    - Can be overridden via ADMIN_USERNAME and ADMIN_PASSWORD env vars
    - If using default password, sets must_change_password=True
    """
    db = get_db()
    with db.session() as session:
        # Check if admin user already exists
        admin = session.query(User).filter(User.username == settings.admin_username).first()
        
        if not admin:
            # Create admin user
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                is_admin=True,
                must_change_password=settings.is_default_admin_password,
            )
            session.add(admin)
            session.flush()
            
            # Create default settings for admin
            admin_settings = UserSettings(
                user_id=admin.id,
                deepseek_api_key=settings.deepseek_api_key or None,
                deepseek_base_url=settings.deepseek_base_url,
                request_delay=settings.request_delay,
            )
            session.add(admin_settings)
            
            print(f"✓ 管理员账户已创建: {settings.admin_username}")
            if settings.is_default_admin_password:
                print("⚠ 使用默认密码，首次登录请修改密码")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("启动 Prof-Finder API 服务...")
    init_admin_user()
    yield
    # Shutdown
    print("关闭 Prof-Finder API 服务...")


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
    
    # Register routers
    app.include_router(auth_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(profiles_router, prefix="/api")
    app.include_router(professors_router, prefix="/api")
    app.include_router(match_router, prefix="/api")
    app.include_router(letters_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    
    @app.get("/api/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "message": "Prof-Finder API is running"}
    
    return app


# Create the app instance
app = create_app()
