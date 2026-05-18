from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ai_copilot import (
    FailureAnalysisResult,
    TestGenerationResult,
    SelectorFixResult,
    ScenarioGenerationResult,
)
from app.services.ai_copilot_service import ai_copilot_service

router = APIRouter()


class AnalyzeRequest(BaseModel):
    test_result_id: int


class GenerateRequest(BaseModel):
    description: str


class SelectorFixRequest(BaseModel):
    selector: str
    context: Optional[str] = None


@router.post("/analyze-failure", response_model=FailureAnalysisResult)
async def analyze_failure(data: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    result = await ai_copilot_service.analyze_failure(db, data.test_result_id)
    return FailureAnalysisResult(**result)


@router.post("/generate-test", response_model=TestGenerationResult)
async def generate_test(data: GenerateRequest):
    result = await ai_copilot_service.generate_test_from_nl(data.description)
    return TestGenerationResult(**result)


@router.post("/fix-selector", response_model=SelectorFixResult)
async def fix_selector(data: SelectorFixRequest):
    result = await ai_copilot_service.auto_fix_selector(data.selector, data.context)
    return SelectorFixResult(**result)


@router.post("/generate-scenario", response_model=ScenarioGenerationResult)
async def generate_scenario(data: GenerateRequest):
    result = await ai_copilot_service.generate_scenario(data.description)
    return ScenarioGenerationResult(**result)
