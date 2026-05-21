from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class QualityReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    overall_score: float
    pass_rate: float
    defect_escape_rate: float
    release_success_rate: float
    device_online_rate: float
    ai_accuracy: float
    dimensions: Any | None
    summary: dict | None
    project_id: int | None
    generated_at: datetime

    class Config:
        from_attributes = True
