from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.quality_gate import QualityGateRuleResponse
from app.services.quality_gate_service import quality_gate_service

router = APIRouter()


@router.get("/rules")
async def get_rules(db: AsyncSession = Depends(get_db)):
    rules = await quality_gate_service.get_rules(db)
    return [QualityGateRuleResponse.model_validate(r).model_dump() for r in rules]


@router.put("/rules")
async def update_rules(data: dict, db: AsyncSession = Depends(get_db)):
    return await quality_gate_service.update_rules(db, data)


@router.get("/status")
async def get_gate_status(db: AsyncSession = Depends(get_db)):
    return await quality_gate_service.get_gate_status(db)
