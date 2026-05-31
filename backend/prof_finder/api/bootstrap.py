"""Application bootstrap helpers."""

from __future__ import annotations

from ..config import settings
from ..db.database import get_db
from ..models.schema import User, UserSettings
from .auth import hash_password


def init_admin_user() -> None:
    """Initialize the admin user if it doesn't exist."""
    db = get_db()
    with db.session() as session:
        admin = session.query(User).filter(User.username == settings.admin_username).first()

        if not admin:
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                is_admin=True,
                must_change_password=settings.is_default_admin_password,
            )
            session.add(admin)
            session.flush()

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
