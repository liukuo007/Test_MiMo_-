from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrafficProfile(Base):
    __tablename__ = "traffic_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    pattern: Mapped[Optional[dict]] = mapped_column(JSON)  # {phases: [{duration_s, rps, ramp_s}]}
    duration_seconds: Mapped[int] = mapped_column(Integer, default=300)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LoadTestRun(Base):
    __tablename__ = "load_test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[Optional[int]] = mapped_column(ForeignKey("traffic_profiles.id"))
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    virtual_device_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/running/completed/failed
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LoadTestMetric(Base):
    __tablename__ = "load_test_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("load_test_runs.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    rps: Mapped[float] = mapped_column(Float, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    error_rate: Mapped[float] = mapped_column(Float, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
