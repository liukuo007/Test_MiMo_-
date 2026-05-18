from __future__ import annotations

import asyncio

import httpx
from celery import shared_task
import structlog

logger = structlog.get_logger()

AI_EVALUATOR_URL = "http://ai-evaluator:8200"


@shared_task(bind=True, max_retries=1)
def run_ai_evaluation(self, evaluation_id: int, model_path: str, dataset_path: str):
    """异步执行 AI 模型评测"""
    logger.info("ai_evaluation_started", evaluation_id=evaluation_id)

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_run_evaluation(evaluation_id, model_path, dataset_path))
        loop.close()
        logger.info("ai_evaluation_completed", evaluation_id=evaluation_id, accuracy=result.get("accuracy"))
        return {"evaluation_id": evaluation_id, **result}
    except Exception as exc:
        logger.error("ai_evaluation_failed", evaluation_id=evaluation_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


async def _run_evaluation(evaluation_id: int, model_path: str, dataset_path: str) -> dict:
    """执行 AI 评测 — 先尝试远程服务，失败回退本地 mock"""
    from sqlalchemy import select
    from app.database import async_session
    from app.models.ai_model import AIEvaluation

    # 尝试调用远程 ai-evaluator 服务
    result = await _call_remote_evaluator(model_path, dataset_path)

    if result is None:
        # 回退到本地 mock 引擎
        result = await _run_local_evaluation(model_path, dataset_path)

    # 持久化评测结果到数据库
    async with async_session() as db:
        res = await db.execute(select(AIEvaluation).where(AIEvaluation.id == evaluation_id))
        ev = res.scalar_one_or_none()
        if ev:
            ev.accuracy = result.get("accuracy", 0)
            ev.recall = result.get("recall", 0)
            ev.f1_score = result.get("f1_score", 0)
            ev.avg_latency_ms = result.get("avg_latency_ms", 0)
            ev.total_samples = result.get("total_samples", 0)
            ev.failed_samples = result.get("failed_samples", 0)
            await db.commit()

    return {
        "status": "completed",
        "accuracy": result.get("accuracy", 0),
        "recall": result.get("recall", 0),
        "f1_score": result.get("f1_score", 0),
        "avg_latency_ms": result.get("avg_latency_ms", 0),
        "total_samples": result.get("total_samples", 0),
        "failed_samples": result.get("failed_samples", 0),
        "failed_cases_count": len(result.get("failed_cases", [])),
    }


async def _call_remote_evaluator(model_path: str, dataset_path: str) -> dict:
    """调用远程 ai-evaluator 服务"""
    try:
        model_version = model_path.split("/")[-1] if "/" in model_path else model_path
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{AI_EVALUATOR_URL}/evaluate", json={
                "model_path": model_path,
                "dataset_name": dataset_path,
                "model_version": model_version or "v2.0",
            })
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.info("remote_evaluator_unavailable", error=str(e))
    return None


async def _run_local_evaluation(model_path: str, dataset_path: str) -> dict:
    """本地 mock 引擎评测"""
    from app.engines.ai_engine import ai_engine

    model_version = model_path.split("/")[-1] if "/" in model_path else model_path
    if not model_version:
        model_version = "v2.0"

    result = await ai_engine.evaluate_model(
        model_path=model_path,
        dataset_path=dataset_path,
        model_version=model_version,
    )

    return {
        "accuracy": result.accuracy,
        "recall": result.recall,
        "f1_score": result.f1_score,
        "avg_latency_ms": result.avg_latency_ms,
        "total_samples": result.total_samples,
        "failed_samples": result.failed_samples,
        "failed_cases": result.failed_cases,
    }
