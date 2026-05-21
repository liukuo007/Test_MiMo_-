from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FlakyTestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    test_case_id: int
    test_case_name: str | None = None
    flaky_rate: float
    pattern: dict | None = None
    status: str
    detected_at: datetime
    resolved_at: datetime | None = None


class FailureClusterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cluster_name: str
    root_cause_category: str
    sample_count: int
    percentage: float
    sample_errors: dict | None = None
    keywords: dict | None = None
    computed_at: datetime


class StabilityTrendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dimension: str
    dimension_value: str
    stability_score: float
    pass_rate: float
    flaky_rate: float
    total_runs: int
    computed_at: datetime


class StabilitySummary(BaseModel):
    total_flaky: int
    active_flaky: int
    resolved_flaky: int
    overall_stability_score: float
    clusters: list[FailureClusterResponse]
    trends: list[StabilityTrendResponse]
