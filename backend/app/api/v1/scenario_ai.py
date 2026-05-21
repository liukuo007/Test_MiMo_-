from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ai_copilot_service import ai_copilot_service
from app.services.scenario_ai_service import scenario_ai_service

router = APIRouter()


class ReplayRequest(BaseModel):
    order_id: str


class GenerateRequest(BaseModel):
    description: str


@router.post("/replay")
async def replay_order(data: ReplayRequest, db: AsyncSession = Depends(get_db)):
    return await scenario_ai_service.replay_order(db, data.order_id)


@router.post("/generate")
async def generate_from_nl(data: GenerateRequest):
    return await ai_copilot_service.generate_scenario(data.description)


@router.get("/preview/{scenario_id}")
async def preview_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    return await scenario_ai_service.preview_scenario(db, scenario_id)
