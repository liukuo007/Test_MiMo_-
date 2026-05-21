from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.test_task import TestTask


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("test_tasks.id"), index=True)
    test_case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_cases.id"))
    status: Mapped[str] = mapped_column(String(16), index=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    device_sn: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(512))
    video_url: Mapped[Optional[str]] = mapped_column(String(512))
    ai_result: Mapped[Optional[dict]] = mapped_column(JSON)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped[TestTask] = relationship(back_populates="results")
