from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, JSON, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)  # SG/US/EU/JP
    name: Mapped[str] = mapped_column(String(64))
    mqtt_broker_url: Mapped[Optional[str]] = mapped_column(String(512))
    payment_endpoint: Mapped[Optional[str]] = mapped_column(String(512))
    ai_endpoint: Mapped[Optional[str]] = mapped_column(String(512))
    base_url: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/inactive/degraded
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RegionMetric(Base):
    __tablename__ = "region_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_code: Mapped[str] = mapped_column(String(8), index=True)
    metric_name: Mapped[str] = mapped_column(String(64))  # health_score/pass_rate/device_online_rate/latency
    metric_value: Mapped[float] = mapped_column(Float, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
