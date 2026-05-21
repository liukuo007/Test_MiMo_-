from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ScenarioTemplateBase(BaseModel):
    name: str
    description: str = ""
    category: str = "shopping"
    icon: str = "ShoppingCart"
    color: str = "#1890ff"
    steps_definition: dict
    params_schema: Optional[dict] = None
    wiremock_mapping: Optional[dict] = None
    sort_order: int = 0
    is_active: bool = True


class ScenarioTemplateCreate(ScenarioTemplateBase):
    pass


class ScenarioTemplateResponse(ScenarioTemplateBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScenarioRunRequest(BaseModel):
    device_sns: list[str] = []
    device_type: Optional[str] = None
    product_key: Optional[str] = None
    quantity: Optional[int] = None
    payment_method: Optional[str] = None
    timeout_seconds: Optional[int] = None


class StepResult(BaseModel):
    step: int
    name: str
    status: str
    duration_ms: float
    detail: str = ""
    error: Optional[str] = None


class ScenarioRunResponse(BaseModel):
    execution_id: int
    batch_id: Optional[int] = None
    template_id: int
    template_name: str
    device_sn: str
    device_name: Optional[str] = None
    is_real_device: bool = False
    run_params: Optional[dict] = None
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
    batch_id: Optional[int] = None
    template_id: int
    template_name: Optional[str] = None
    device_sn: str
    device_name: Optional[str] = None
    is_real_device: bool = False
    run_params: Optional[Any] = None
    status: str
    steps_result: Optional[Any] = None
    total_duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    triggered_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    template_id: int
    template_name: Optional[str] = None
    name: str
    total_count: int
    passed_count: int
    failed_count: int
    status: str
    run_params: Optional[Any] = None
    triggered_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DevicePickItem(BaseModel):
    id: int
    device_sn: str
    name: str
    device_type: str
    status: str
    region: Optional[str] = None
    temperature: Optional[float] = None
    last_heartbeat: Optional[datetime] = None
    firmware_version: Optional[str] = None
