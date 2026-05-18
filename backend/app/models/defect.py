from __future__ import annotations
from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DefectStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    CLOSED = "closed"
    REOPENED = "reopened"


class DefectPriority(str, enum.Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class DefectSource(str, enum.Enum):
    TEST = "test"
    AUTO = "auto"
    USER = "user"
    MONITOR = "monitor"


# 合法的状态流转
VALID_TRANSITIONS = {
    DefectStatus.NEW: [DefectStatus.IN_PROGRESS],
    DefectStatus.IN_PROGRESS: [DefectStatus.FIXED, DefectStatus.CLOSED],
    DefectStatus.FIXED: [DefectStatus.CLOSED, DefectStatus.REOPENED],
    DefectStatus.REOPENED: [DefectStatus.IN_PROGRESS],
    DefectStatus.CLOSED: [],
}


class Defect(Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[DefectStatus] = mapped_column(
        Enum(DefectStatus), default=DefectStatus.NEW, index=True
    )
    priority: Mapped[DefectPriority] = mapped_column(
        Enum(DefectPriority), default=DefectPriority.P2, index=True
    )
    source: Mapped[DefectSource] = mapped_column(
        Enum(DefectSource), default=DefectSource.USER
    )
    device_sn: Mapped[Optional[str]] = mapped_column(String(64))
    test_case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_cases.id"))
    test_result_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_results.id"))
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(512))
    tags: Mapped[Optional[dict]] = mapped_column(JSON)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    test_case: Mapped["Optional[TestCase]"] = relationship(foreign_keys=[test_case_id])
    test_result: Mapped["Optional[TestResult]"] = relationship(foreign_keys=[test_result_id])
    assignee: Mapped["Optional[User]"] = relationship(foreign_keys=[assigned_to])
    creator: Mapped["Optional[User]"] = relationship(foreign_keys=[created_by])
