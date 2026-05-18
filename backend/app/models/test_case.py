from __future__ import annotations
from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TestType(str, enum.Enum):
    API = "api"
    IOT = "iot"
    AI = "ai"
    WEB = "web"
    APP = "app"
    E2E = "e2e"


class Priority(str, enum.Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    test_type: Mapped[TestType] = mapped_column(Enum(TestType))
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.P1)
    module: Mapped[Optional[str]] = mapped_column(String(128))
    steps: Mapped[Optional[dict]] = mapped_column(JSON)
    expected_result: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(JSON)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="test_cases")
