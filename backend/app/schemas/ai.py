from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AIModelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str


class AIModelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    model_type: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class AIModelVersionCreate(BaseModel):
    model_id: int
    version: str
    path: str


class AIModelVersionResponse(BaseModel):
    id: int
    model_id: int
    version: str
    path: str
    metrics: Optional[dict]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AICompareRequest(BaseModel):
    model_a_version: str
    model_b_version: str
    dataset_path: str = "medium"


class AIEvaluationCreate(BaseModel):
    model_version_id: int
    dataset_name: str


class AIEvaluationResponse(BaseModel):
    id: int
    model_version_id: int
    dataset_name: str
    accuracy: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    avg_latency_ms: Optional[float]
    total_samples: int
    failed_samples: int
    report_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
