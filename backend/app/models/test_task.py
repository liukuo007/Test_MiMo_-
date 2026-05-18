from __future__ import annotations
from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, enum.Enum):
    MANUAL = "manual"
    CRON = "cron"
    CI_CD = "ci_cd"
    WEBHOOK = "webhook"


class TestTask(Base):
    __tablename__ = "test_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    trigger_type: Mapped[TriggerType] = mapped_column(Enum(TriggerType), default=TriggerType.MANUAL)
    environment: Mapped[str] = mapped_column(String(32))
    branch: Mapped[Optional[str]] = mapped_column(String(128))
    dag_config: Mapped[Optional[dict]] = mapped_column(JSON)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="test_tasks")
    steps: Mapped[list["TestTaskStep"]] = relationship(back_populates="task")
    results: Mapped[list["TestResult"]] = relationship(back_populates="task")


class TestTaskStep(Base):
    __tablename__ = "test_task_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("test_tasks.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    step_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    order: Mapped[int] = mapped_column(Integer)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    task: Mapped["TestTask"] = relationship(back_populates="steps")
