from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EnvironmentBase(BaseModel):
    name: str
    env_type: str = "staging"
    region: Optional[str] = None
    base_url: Optional[str] = None
    mqtt_broker_url: Optional[str] = None
    db_url: Optional[str] = None
    redis_url: Optional[str] = None
    ai_evaluator_url: Optional[str] = None
    wiremock_url: Optional[str] = None
    payment_endpoint: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    env_type: Optional[str] = None
    region: Optional[str] = None
    base_url: Optional[str] = None
    mqtt_broker_url: Optional[str] = None
    db_url: Optional[str] = None
    redis_url: Optional[str] = None
    ai_evaluator_url: Optional[str] = None
    wiremock_url: Optional[str] = None
    payment_endpoint: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None


class EnvironmentResponse(EnvironmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    env_id: int
    component: str
    status: str
    latency_ms: Optional[float] = None
    details: Optional[dict] = None
    checked_at: datetime


class SnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    env_id: int
    name: str
    snapshot_type: str
    state_data: Optional[dict] = None
    notes: Optional[str] = None
    created_at: datetime


class SnapshotCreate(BaseModel):
    name: str
    snapshot_type: str = "manual"
    notes: Optional[str] = None


class EnvironmentHealthSummary(BaseModel):
    environment: EnvironmentResponse
    health_checks: list[HealthCheckResponse]
    overall_status: str
