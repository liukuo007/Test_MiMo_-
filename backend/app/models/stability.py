from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FlakyTestCase(Base):
    __tablename__ = "flaky_test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), index=True)
    flaky_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1
    pattern: Mapped[Optional[dict]] = mapped_column(JSON)  # e.g. {"type": "pass_fail_pass", "occurrences": 5}
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/ignored/resolved
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class FailureCluster(Base):
    __tablename__ = "failure_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_name: Mapped[str] = mapped_column(String(128))
    root_cause_category: Mapped[str] = mapped_column(String(64))  # mqtt_timeout/ai_misprediction/payment_failure/network_error/config_issue/data_corruption
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    sample_errors: Mapped[Optional[dict]] = mapped_column(JSON)  # list of sample error messages
    keywords: Mapped[Optional[dict]] = mapped_column(JSON)  # extracted keywords
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StabilityTrend(Base):
    __tablename__ = "stability_trends"

    id: Mapped[int] = mapped_column(primary_key=True)
    dimension: Mapped[str] = mapped_column(String(64))  # overall/device_type/env/region
    dimension_value: Mapped[str] = mapped_column(String(128))
    stability_score: Mapped[float] = mapped_column(Float, default=100.0)  # 0-100
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0)
    flaky_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
