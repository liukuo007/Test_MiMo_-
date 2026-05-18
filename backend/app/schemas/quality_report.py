from __future__ import annotations
from typing import Optional, Any

from datetime import datetime

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
    dimensions: Optional[Any]
    summary: Optional[dict]
    project_id: Optional[int]
    generated_at: datetime

    class Config:
        from_attributes = True
