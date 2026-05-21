from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TestResultResponse(BaseModel):
    id: int
    task_id: int
    test_case_id: int | None
    status: str
    duration_ms: int | None
    error_message: str | None
    trace_id: str | None
    device_sn: str | None
    screenshot_url: str | None
    video_url: str | None
    ai_result: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
