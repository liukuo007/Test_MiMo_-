from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RegionBase(BaseModel):
    code: str
    name: str
    mqtt_broker_url: Optional[str] = None
    payment_endpoint: Optional[str] = None
    ai_endpoint: Optional[str] = None
    base_url: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    name: Optional[str] = None
    mqtt_broker_url: Optional[str] = None
    payment_endpoint: Optional[str] = None
    ai_endpoint: Optional[str] = None
    base_url: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None


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
