from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class QualityGateRuleCreate(BaseModel):
    name: str
    metric: str
    threshold: float
    operator: str = "gte"
    is_active: bool = True
    project_id: int | None = None


class QualityGateRuleUpdate(BaseModel):
    name: str | None = None
    threshold: float | None = None
    operator: str | None = None
    is_active: bool | None = None


class QualityGateRuleResponse(BaseModel):
    id: int
    name: str
    metric: str
    threshold: float
    operator: str
    is_active: bool
    project_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
