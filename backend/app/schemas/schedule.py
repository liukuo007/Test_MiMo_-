from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    name: str
    task_id: int
    cron_expression: str


class ScheduleUpdate(BaseModel):
    name: str | None = None
    cron_expression: str | None = None
    is_active: bool | None = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    task_id: int
    cron_expression: str
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
