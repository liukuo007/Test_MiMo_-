from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AIModelCreate(BaseModel):
    name: str
    description: str | None = None
    model_type: str


class AIModelResponse(BaseModel):
    id: int
    name: str
    description: str | None
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
    metrics: dict | None
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
    accuracy: float | None
    recall: float | None
    f1_score: float | None
    avg_latency_ms: float | None
    total_samples: int
    failed_samples: int
    report_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True
