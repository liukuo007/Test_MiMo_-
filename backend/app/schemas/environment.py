from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnvironmentBase(BaseModel):
    name: str
    env_type: str = "staging"
    region: str | None = None
    base_url: str | None = None
    mqtt_broker_url: str | None = None
    db_url: str | None = None
    redis_url: str | None = None
    ai_evaluator_url: str | None = None
    wiremock_url: str | None = None
    payment_endpoint: str | None = None
    config: dict | None = None
    description: str | None = None


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(BaseModel):
    name: str | None = None
    env_type: str | None = None
    region: str | None = None
    base_url: str | None = None
    mqtt_broker_url: str | None = None
    db_url: str | None = None
    redis_url: str | None = None
    ai_evaluator_url: str | None = None
    wiremock_url: str | None = None
    payment_endpoint: str | None = None
    status: str | None = None
    config: dict | None = None
    description: str | None = None


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
    latency_ms: float | None = None
    details: dict | None = None
    checked_at: datetime


class SnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    env_id: int
    name: str
    snapshot_type: str
    state_data: dict | None = None
    notes: str | None = None
    created_at: datetime


class SnapshotCreate(BaseModel):
    name: str
    snapshot_type: str = "manual"
    notes: str | None = None


class EnvironmentHealthSummary(BaseModel):
    environment: EnvironmentResponse
    health_checks: list[HealthCheckResponse]
    overall_status: str
