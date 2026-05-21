from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ScenarioTemplateBase(BaseModel):
    name: str
    description: str = ""
    category: str = "shopping"
    icon: str = "ShoppingCart"
    color: str = "#1890ff"
    steps_definition: dict
    params_schema: dict | None = None
    wiremock_mapping: dict | None = None
    sort_order: int = 0
    is_active: bool = True


class ScenarioTemplateCreate(ScenarioTemplateBase):
    pass


class ScenarioTemplateResponse(ScenarioTemplateBase):
    id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ScenarioRunRequest(BaseModel):
    device_sns: list[str] = []
    device_type: str | None = None
    product_key: str | None = None
    quantity: int | None = None
    payment_method: str | None = None
    timeout_seconds: int | None = None


class StepResult(BaseModel):
    step: int
    name: str
    status: str
    duration_ms: float
    detail: str = ""
    error: str | None = None


class ScenarioRunResponse(BaseModel):
    execution_id: int
    batch_id: int | None = None
    template_id: int
    template_name: str
    device_sn: str
    device_name: str | None = None
    is_real_device: bool = False
    run_params: dict | None = None
    status: str
    total_duration_ms: float
    steps: list[StepResult]


class BatchRunResponse(BaseModel):
    batch_id: int
    template_id: int
    template_name: str
    total_count: int
    status: str
    executions: list[ScenarioRunResponse]


class ScenarioExecutionResponse(BaseModel):
    id: int
    batch_id: int | None = None
    template_id: int
    template_name: str | None = None
    device_sn: str
    device_name: str | None = None
    is_real_device: bool = False
    run_params: Any | None = None
    status: str
    steps_result: Any | None = None
    total_duration_ms: float | None = None
    error_message: str | None = None
    triggered_by_name: str | None = None
    created_at: datetime | None = None
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    template_id: int
    template_name: str | None = None
    name: str
    total_count: int
    passed_count: int
    failed_count: int
    status: str
    run_params: Any | None = None
    triggered_by_name: str | None = None
    created_at: datetime | None = None
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class DevicePickItem(BaseModel):
    id: int
    device_sn: str
    name: str
    device_type: str
    status: str
    region: str | None = None
    temperature: float | None = None
    last_heartbeat: datetime | None = None
    firmware_version: str | None = None
