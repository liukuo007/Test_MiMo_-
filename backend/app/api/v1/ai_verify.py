from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import CurrentUser
from app.engines.ai_engine import ai_engine
from app.models.ai_model import AIEvaluation, AIModel, AIModelVersion
from app.schemas.ai import (
    AICompareRequest,
    AIEvaluationCreate,
    AIEvaluationResponse,
    AIModelCreate,
    AIModelResponse,
    AIModelVersionCreate,
    AIModelVersionResponse,
)

router = APIRouter()


# ===== 模型管理 =====

@router.get("/models", response_model=list[AIModelResponse])
async def list_ai_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).order_by(AIModel.id.desc()))
    return result.scalars().all()


@router.post("/models", response_model=AIModelResponse)
async def create_ai_model(req: AIModelCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    model = AIModel(**req.model_dump(), created_by=int(current_user["sub"]))
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return model


@router.get("/models/{model_id}/versions", response_model=list[AIModelVersionResponse])
async def list_model_versions(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AIModelVersion).where(AIModelVersion.model_id == model_id).order_by(AIModelVersion.id.desc())
    )
    return result.scalars().all()


@router.post("/models/versions", response_model=AIModelVersionResponse)
async def create_model_version(req: AIModelVersionCreate, db: AsyncSession = Depends(get_db)):
    version = AIModelVersion(**req.model_dump())
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version


# ===== 评测管理 =====

@router.get("/evaluations", response_model=list[AIEvaluationResponse])
async def list_evaluations(
    db: AsyncSession = Depends(get_db),
    model_version_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(AIEvaluation)
    if model_version_id:
        query = query.where(AIEvaluation.model_version_id == model_version_id)
    query = query.offset(skip).limit(limit).order_by(AIEvaluation.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/evaluations", response_model=AIEvaluationResponse)
async def create_evaluation(req: AIEvaluationCreate, db: AsyncSession = Depends(get_db)):
    version_result = await db.execute(
        select(AIModelVersion).where(AIModelVersion.id == req.model_version_id)
    )
    version = version_result.scalar_one_or_none()
    model_path = version.path if version else "default"

    evaluation = AIEvaluation(
        model_version_id=req.model_version_id,
        dataset_name=req.dataset_name,
        total_samples=0,
        failed_samples=0,
    )
    db.add(evaluation)
    await db.flush()
    await db.refresh(evaluation)

    eval_id = evaluation.id
    celery_app.send_task(
        "app.tasks.ai_evaluation.run_ai_evaluation",
        args=[eval_id, model_path, req.dataset_name],
        queue="ai",
    )

    return evaluation


@router.get("/evaluations/{eval_id}", response_model=AIEvaluationResponse)
async def get_evaluation(eval_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIEvaluation).where(AIEvaluation.id == eval_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise NotFoundError("Evaluation", eval_id)
    return evaluation


@router.post("/compare")
async def compare_models(req: AICompareRequest):
    """对比两个 AI 模型版本"""
    return await ai_engine.compare_models(
        model_a_version=req.model_a_version,
        model_b_version=req.model_b_version,
        dataset_path=req.dataset_path,
    )
