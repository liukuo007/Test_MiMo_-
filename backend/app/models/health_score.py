from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HealthScoreSnapshot(Base):
    __tablename__ = "health_score_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)
    region: Mapped[Optional[str]] = mapped_column(String(32))
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    dimensions: Mapped[Optional[dict]] = mapped_column(JSON)
    release_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
