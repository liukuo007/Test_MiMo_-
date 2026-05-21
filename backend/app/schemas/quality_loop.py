from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class QualityLoopRuleBase(BaseModel):
    name: str
    trigger_metric: str
    threshold: float
    operator: str = "<"
    action_chain: Optional[dict] = None
    enabled: bool = True


class QualityLoopRuleCreate(QualityLoopRuleBase):
    pass


class QualityLoopRuleUpdate(BaseModel):
    name: Optional[str] = None
    trigger_metric: Optional[str] = None
    threshold: Optional[float] = None
    operator: Optional[str] = None
    action_chain: Optional[dict] = None
    enabled: Optional[bool] = None


class QualityLoopRuleResponse(QualityLoopRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class QualityLoopExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rule_id: int
    rule_name: Optional[str] = None
    trigger_value: float
    current_step: int
    total_steps: int
    status: str
    steps_log: Optional[dict] = None
    defect_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
