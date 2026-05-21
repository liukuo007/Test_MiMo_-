from __future__ import annotations

from pydantic import BaseModel


class FailureAnalysisResult(BaseModel):
    test_result_id: int
    root_cause: str
    category: str
    confidence: float
    related_events: list[dict]
    related_traces: list[dict]
    suggestion: str


class TestGenerationResult(BaseModel):
    description: str
    steps: list[dict]
    estimated_duration_ms: int
    suggested_devices: list[str]


class SelectorFixResult(BaseModel):
    original_selector: str
    selector_type: str
    suggested_fixes: list[dict]
    confidence: float


class ScenarioGenerationResult(BaseModel):
    name: str
    description: str
    steps: list[dict]
    source: str = "ai_generated"
