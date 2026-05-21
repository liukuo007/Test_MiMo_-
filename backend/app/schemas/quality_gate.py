from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QualityGateRuleCreate(BaseModel):
    name: str
    metric: str
    threshold: float
    operator: str = "gte"
    is_active: bool = True
    project_id: Optional[int] = None


class QualityGateRuleUpdate(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    operator: Optional[str] = None
    is_active: Optional[bool] = None


class QualityGateRuleResponse(BaseModel):
    id: int
    name: str
    metric: str
    threshold: float
    operator: str
    is_active: bool
    project_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
