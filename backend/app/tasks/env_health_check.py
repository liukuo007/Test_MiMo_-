from __future__ import annotations

import asyncio

from celery import shared_task
from sqlalchemy import select

from app.database import async_session
from app.models.environment import Environment
from app.services.environment_service import environment_service


@shared_task(name="app.tasks.env_health_check.env_health_check_all")
def env_health_check_all():
    """Periodic health check for all environments. Runs every 5 minutes."""

    async def _run():
        async with async_session() as db:
            result = await db.execute(select(Environment))
            envs = list(result.scalars().all())
            for env in envs:
                try:
                    await environment_service.check_health(db, env.id)
                except Exception as e:
                    print(f"[env_health_check] env={env.id} error: {e}")

    asyncio.run(_run())
    return {"checked": True}
