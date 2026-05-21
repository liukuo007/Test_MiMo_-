from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScenarioTemplate(Base):
    __tablename__ = "scenario_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="shopping")
    icon: Mapped[str] = mapped_column(String(32), default="ShoppingCart")
    color: Mapped[str] = mapped_column(String(16), default="#1890ff")
    steps_definition: Mapped[dict] = mapped_column(JSON)
    params_schema: Mapped[dict | None] = mapped_column(JSON)
    wiremock_mapping: Mapped[dict | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    source: Mapped[str] = mapped_column(String(32), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    executions: Mapped[list[ScenarioExecution]] = relationship(back_populates="template")


class ExecutionStatus(str, enum.Enum):
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class BatchStatus(str, enum.Enum):
    RUNNING = "running"
    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"


class ScenarioBatch(Base):
    __tablename__ = "scenario_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("scenario_templates.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    total_count: Mapped[int] = mapped_column(Integer)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.RUNNING)
    run_params: Mapped[dict | None] = mapped_column(JSON)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    triggered_by_name: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    template: Mapped[ScenarioTemplate] = relationship()
    executions: Mapped[list[ScenarioExecution]] = relationship(back_populates="batch")


class ScenarioExecution(Base):
    __tablename__ = "scenario_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("scenario_batches.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("scenario_templates.id"), index=True)
    device_sn: Mapped[str] = mapped_column(String(64))
    device_name: Mapped[str | None] = mapped_column(String(128))
    is_real_device: Mapped[bool] = mapped_column(default=False)
    run_params: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.RUNNING)
    steps_result: Mapped[dict | None] = mapped_column(JSON)
    total_duration_ms: Mapped[float | None] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    triggered_by_name: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    template: Mapped[ScenarioTemplate] = relationship(back_populates="executions")
    batch: Mapped[ScenarioBatch | None] = relationship(back_populates="executions")
