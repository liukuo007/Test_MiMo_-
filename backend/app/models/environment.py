from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    env_type: Mapped[str] = mapped_column(String(32), default="staging")  # dev/staging/prod
    region: Mapped[Optional[str]] = mapped_column(String(32))
    base_url: Mapped[Optional[str]] = mapped_column(String(512))
    mqtt_broker_url: Mapped[Optional[str]] = mapped_column(String(512))
    db_url: Mapped[Optional[str]] = mapped_column(String(512))
    redis_url: Mapped[Optional[str]] = mapped_column(String(512))
    ai_evaluator_url: Mapped[Optional[str]] = mapped_column(String(512))
    wiremock_url: Mapped[Optional[str]] = mapped_column(String(512))
    payment_endpoint: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="unknown")  # healthy/degraded/down/unknown
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    snapshots: Mapped[list["EnvironmentSnapshot"]] = relationship(back_populates="environment", cascade="all, delete-orphan")
    health_checks: Mapped[list["EnvironmentHealthCheck"]] = relationship(back_populates="environment", cascade="all, delete-orphan")


class EnvironmentSnapshot(Base):
    __tablename__ = "environment_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    env_id: Mapped[int] = mapped_column(ForeignKey("environments.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    snapshot_type: Mapped[str] = mapped_column(String(32), default="manual")  # manual/auto/freeze
    state_data: Mapped[Optional[dict]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    environment: Mapped["Environment"] = relationship(back_populates="snapshots")


class EnvironmentHealthCheck(Base):
    __tablename__ = "environment_health_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    env_id: Mapped[int] = mapped_column(ForeignKey("environments.id"), index=True)
    component: Mapped[str] = mapped_column(String(64))  # redis/postgres/mqtt/wiremock/ai/payment
    status: Mapped[str] = mapped_column(String(16))  # healthy/degraded/down
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    checked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    environment: Mapped["Environment"] = relationship(back_populates="health_checks")
