from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QualityLoopRule(Base):
    __tablename__ = "quality_loop_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    trigger_metric: Mapped[str] = mapped_column(String(64))  # health_score/pass_rate/flaky_rate/crash_rate
    threshold: Mapped[float] = mapped_column(Float)
    operator: Mapped[str] = mapped_column(String(8), default="<")  # < / > / <= / >=
    action_chain: Mapped[Optional[dict]] = mapped_column(JSON)  # ordered list of actions
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class QualityLoopExecution(Base):
    __tablename__ = "quality_loop_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("quality_loop_rules.id"), index=True)
    trigger_value: Mapped[float] = mapped_column(Float)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="running")  # running/completed/failed/cancelled
    steps_log: Mapped[Optional[dict]] = mapped_column(JSON)  # list of step results
    defect_id: Mapped[Optional[int]] = mapped_column(ForeignKey("defects.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
