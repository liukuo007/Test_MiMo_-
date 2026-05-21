from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DevicePool(Base):
    __tablename__ = "device_pools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    pool_type: Mapped[str] = mapped_column(String(32), default="manual")  # manual/auto
    auto_assign: Mapped[bool] = mapped_column(Boolean, default=False)
    max_devices: Mapped[int] = mapped_column(Integer, default=0)  # 0 = unlimited
    description: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    members: Mapped[list[DevicePoolMember]] = relationship(back_populates="pool", cascade="all, delete-orphan")


class DevicePoolMember(Base):
    __tablename__ = "device_pool_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("device_pools.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pool: Mapped[DevicePool] = relationship(back_populates="members")


class DeviceTag(Base):
    __tablename__ = "device_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    tag_key: Mapped[str] = mapped_column(String(64))
    tag_value: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DeviceHealthScore(Base):
    __tablename__ = "device_health_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), unique=True, index=True)
    score: Mapped[float] = mapped_column(Float, default=100.0)
    factors: Mapped[dict | None] = mapped_column(JSON)  # uptime, heartbeat_freshness, temperature, error_rate
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
