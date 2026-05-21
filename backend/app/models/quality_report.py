from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    report_type: Mapped[str] = mapped_column(String(32), default="weekly")
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    pass_rate: Mapped[float] = mapped_column(Float, default=0)
    defect_escape_rate: Mapped[float] = mapped_column(Float, default=0)
    release_success_rate: Mapped[float] = mapped_column(Float, default=0)
    device_online_rate: Mapped[float] = mapped_column(Float, default=0)
    ai_accuracy: Mapped[float] = mapped_column(Float, default=0)
    dimensions: Mapped[dict | None] = mapped_column(JSON)
    summary: Mapped[dict | None] = mapped_column(JSON)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
