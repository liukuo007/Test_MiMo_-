from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegionBase(BaseModel):
    code: str
    name: str
    mqtt_broker_url: str | None = None
    payment_endpoint: str | None = None
    ai_endpoint: str | None = None
    base_url: str | None = None
    config: dict | None = None
    description: str | None = None


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    name: str | None = None
    mqtt_broker_url: str | None = None
    payment_endpoint: str | None = None
    ai_endpoint: str | None = None
    base_url: str | None = None
    status: str | None = None
    config: dict | None = None
    description: str | None = None


class RegionResponse(RegionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime


class RegionMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    region_code: str
    metric_name: str
    metric_value: float
    computed_at: datetime


class RegionHealthSummary(BaseModel):
    region: RegionResponse
    metrics: dict[str, float]
    overall_score: float
