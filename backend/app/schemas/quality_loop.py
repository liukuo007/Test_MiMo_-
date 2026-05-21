from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QualityLoopRuleBase(BaseModel):
    name: str
    trigger_metric: str
    threshold: float
    operator: str = "<"
    action_chain: dict | None = None
    enabled: bool = True


class QualityLoopRuleCreate(QualityLoopRuleBase):
    pass


class QualityLoopRuleUpdate(BaseModel):
    name: str | None = None
    trigger_metric: str | None = None
    threshold: float | None = None
    operator: str | None = None
    action_chain: dict | None = None
    enabled: bool | None = None


class QualityLoopRuleResponse(QualityLoopRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class QualityLoopExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rule_id: int
    rule_name: str | None = None
    trigger_value: float
    current_step: int
    total_steps: int
    status: str
    steps_log: dict | None = None
    defect_id: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
