from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.project import Environment


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    environment: Environment = Environment.DEV


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    environment: Environment | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    environment: Environment
    owner_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
