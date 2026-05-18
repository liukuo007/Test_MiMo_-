from __future__ import annotations

import asyncio
import structlog

from app.celery_app import celery_app
from app.database import async_session
from app.models.health_score import HealthScoreSnapshot
from app.services.health_score_service import health_score_service

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.health_snapshot.compute_health_snapshot")
def compute_health_snapshot():
    """定时计算健康分快照"""
    asyncio.run(_compute())


async def _compute():
    async with async_session() as db:
        try:
            result = await health_score_service.compute_health_score(db)

            snapshot = HealthScoreSnapshot(
                overall_score=result.overall_score,
                dimensions={
                    d.key: {
                        "name": d.name,
                        "weight": d.weight,
                        "value": d.value,
                        "score": round(d.score, 2),
                        "status": d.status,
                    }
                    for d in result.dimensions
                },
                release_allowed=result.release_allowed,
            )
            db.add(snapshot)
            await db.commit()
            logger.info("health_snapshot_computed", score=result.overall_score, release=result.release_allowed)
        except Exception as e:
            logger.error("health_snapshot_failed", error=str(e))
            await db.rollback()
