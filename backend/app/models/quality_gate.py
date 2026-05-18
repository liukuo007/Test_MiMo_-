from __future__ import annotations
from typing import Optional

from datetime import datetime

from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QualityGateRule(Base):
    __tablename__ = "quality_gate_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    metric: Mapped[str] = mapped_column(String(64), index=True)
    threshold: Mapped[float] = mapped_column(Float)
    operator: Mapped[str] = mapped_column(String(16), default="gte")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
