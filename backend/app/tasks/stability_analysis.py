from __future__ import annotations

import asyncio

from celery import shared_task


@shared_task(name="app.tasks.stability_analysis.run_stability_analysis")
def run_stability_analysis():
    """Daily stability analysis: detect flaky tests, cluster failures, compute trends."""

    async def _run():
        from app.database import async_session
        from app.services.stability_service import stability_service

        async with async_session() as db:
            flaky = await stability_service.detect_flaky_tests(db)
            clusters = await stability_service.cluster_failures(db)
            trends = await stability_service.compute_stability_trends(db)
            print(f"[stability] flaky={len(flaky)} clusters={len(clusters)} trends={len(trends)}")

    asyncio.run(_run())
    return {"analyzed": True}
