from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.quality_loop import (
    QualityLoopExecutionResponse,
    QualityLoopRuleCreate,
    QualityLoopRuleResponse,
    QualityLoopRuleUpdate,
)
from app.services.quality_loop_service import quality_loop_service

router = APIRouter()


@router.get("/rules", response_model=list[QualityLoopRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    return await quality_loop_service.list_rules(db)


@router.post("/rules", response_model=QualityLoopRuleResponse)
async def create_rule(data: QualityLoopRuleCreate, db: AsyncSession = Depends(get_db)):
    return await quality_loop_service.create_rule(db, data.model_dump())


@router.get("/rules/{rule_id}", response_model=QualityLoopRuleResponse)
async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    rule = await quality_loop_service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=QualityLoopRuleResponse)
async def update_rule(rule_id: int, data: QualityLoopRuleUpdate, db: AsyncSession = Depends(get_db)):
    rule = await quality_loop_service.update_rule(db, rule_id, data.model_dump(exclude_unset=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    ok = await quality_loop_service.delete_rule(db, rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"ok": True}


@router.post("/rules/{rule_id}/trigger")
async def manual_trigger(rule_id: int, db: AsyncSession = Depends(get_db)):
    execution = await quality_loop_service.manual_trigger(db, rule_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Rule not found or trigger failed")
    resp = QualityLoopExecutionResponse.model_validate(execution)
    # Enrich with rule_name
    rule = await quality_loop_service.get_rule(db, execution.rule_id)
    if rule:
        resp.rule_name = rule.name
    return resp


@router.get("/executions")
async def list_executions(
    rule_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await quality_loop_service.list_executions(db, rule_id=rule_id, status=status)


@router.post("/evaluate")
async def evaluate_rules(db: AsyncSession = Depends(get_db)):
    executions = await quality_loop_service.evaluate_rules(db)
    return {"triggered": len(executions)}
