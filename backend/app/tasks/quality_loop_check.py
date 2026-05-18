from __future__ import annotations

import asyncio

from celery import shared_task


@shared_task(name="app.tasks.quality_loop_check.evaluate_quality_loop_rules")
def evaluate_quality_loop_rules():
    """Periodic check: evaluate all quality loop rules. Runs every 15 minutes."""

    async def _run():
        from app.database import async_session
        from app.services.quality_loop_service import quality_loop_service

        async with async_session() as db:
            executions = await quality_loop_service.evaluate_rules(db)
            print(f"[quality_loop] triggered {len(executions)} executions")

    asyncio.run(_run())
    return {"evaluated": True}
