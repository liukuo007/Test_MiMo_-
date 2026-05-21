from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.project import Environment


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    environment: Environment = Environment.DEV


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[Environment] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    environment: Environment
    owner_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
