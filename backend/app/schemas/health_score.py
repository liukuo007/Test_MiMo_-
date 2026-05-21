from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DimensionDetail(BaseModel):
    name: str
    key: str
    weight: float
    value: float
    score: float
    status: str


class HealthScoreResponse(BaseModel):
    overall_score: float
    release_allowed: bool
    release_threshold: float
    dimensions: list[DimensionDetail]
    computed_at: datetime | None = None


class HealthScoreTrendItem(BaseModel):
    overall_score: float
    release_allowed: bool
    computed_at: datetime


class HealthScoreTrend(BaseModel):
    items: list[HealthScoreTrendItem]


class ReleaseGateResponse(BaseModel):
    release_allowed: bool
    overall_score: float
    threshold: float
    failing_dimensions: list[str]
