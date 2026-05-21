from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TestResultResponse(BaseModel):
    id: int
    task_id: int
    test_case_id: Optional[int]
    status: str
    duration_ms: Optional[int]
    error_message: Optional[str]
    trace_id: Optional[str]
    device_sn: Optional[str]
    screenshot_url: Optional[str]
    video_url: Optional[str]
    ai_result: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
