from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrafficProfileBase(BaseModel):
    name: str
    pattern: dict | None = None
    duration_seconds: int = 300
    description: str | None = None


class TrafficProfileCreate(TrafficProfileBase):
    pass


class TrafficProfileResponse(TrafficProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class LoadTestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int | None = None
    profile_name: str | None = None
    device_count: int
    virtual_device_count: int
    status: str
    total_requests: int
    error_count: int
    avg_latency_ms: float
    p99_latency_ms: float
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class LoadTestMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: int
    timestamp: datetime
    rps: float
    avg_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    active_users: int


class RunLoadTestRequest(BaseModel):
    profile_id: int
    device_count: int = 0
    virtual_device_count: int = 100
