"""BackgroundTask model for persistent task state."""

from ..utils.time import utc_now
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .schema import Base


class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), unique=True, nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    task_name = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    total = Column(Integer, nullable=False, default=0)
    current = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    message = Column(Text, default="")
    error_message = Column(Text, default="")
    results = Column(JSON, default=list)
    cancel_requested = Column(Boolean, default=False)
    enqueue_args = Column(JSON, default=list)
    enqueue_kwargs = Column(JSON, default=dict)
    parent_task_id = Column(String(36), ForeignKey("background_tasks.task_id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    user = relationship("User", backref="background_tasks")
