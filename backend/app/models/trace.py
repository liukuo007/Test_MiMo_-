from __future__ import annotations
from typing import Optional

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    root_span_id: Mapped[Optional[str]] = mapped_column(String(64))
    service: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TraceSpan(Base):
    __tablename__ = "trace_spans"

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    span_id: Mapped[str] = mapped_column(String(64), index=True)
    parent_span_id: Mapped[Optional[str]] = mapped_column(String(64))
    service: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[Optional[dict]] = mapped_column(JSON)
    logs: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
