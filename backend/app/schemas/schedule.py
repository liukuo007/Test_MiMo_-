from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    name: str
    task_id: int
    cron_expression: str


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    task_id: int
    cron_expression: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
