from __future__ import annotations

import random
from datetime import datetime
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.load_test import TrafficProfile, LoadTestRun, LoadTestMetric


class LoadTestService:

    async def list_profiles(self, db: AsyncSession) -> list[TrafficProfile]:
        result = await db.execute(select(TrafficProfile).order_by(TrafficProfile.id))
        return list(result.scalars().all())

    async def get_profile(self, db: AsyncSession, profile_id: int) -> Optional[TrafficProfile]:
        result = await db.execute(select(TrafficProfile).where(TrafficProfile.id == profile_id))
        return result.scalar_one_or_none()

    async def create_profile(self, db: AsyncSession, data: dict) -> TrafficProfile:
        profile = TrafficProfile(**data)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def delete_profile(self, db: AsyncSession, profile_id: int) -> bool:
        profile = await self.get_profile(db, profile_id)
        if not profile:
            return False
        await db.delete(profile)
        await db.commit()
        return True

    async def create_run(self, db: AsyncSession, profile_id: int, device_count: int, virtual_count: int) -> LoadTestRun:
        run = LoadTestRun(
            profile_id=profile_id,
            device_count=device_count,
            virtual_device_count=virtual_count,
            status="pending",
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run

    async def get_run(self, db: AsyncSession, run_id: int) -> Optional[LoadTestRun]:
        result = await db.execute(select(LoadTestRun).where(LoadTestRun.id == run_id))
        return result.scalar_one_or_none()

    async def list_runs(self, db: AsyncSession, limit: int = 20) -> list[dict]:
        result = await db.execute(
            select(LoadTestRun).order_by(desc(LoadTestRun.created_at)).limit(limit)
        )
        runs = list(result.scalars().all())
        enriched = []
        for run in runs:
            profile = None
            if run.profile_id:
                profile = await self.get_profile(db, run.profile_id)
            enriched.append({
                "id": run.id,
                "profile_id": run.profile_id,
                "profile_name": profile.name if profile else None,
                "device_count": run.device_count,
                "virtual_device_count": run.virtual_device_count,
                "status": run.status,
                "total_requests": run.total_requests,
                "error_count": run.error_count,
                "avg_latency_ms": run.avg_latency_ms,
                "p99_latency_ms": run.p99_latency_ms,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "created_at": run.created_at,
            })
        return enriched

    async def get_run_metrics(self, db: AsyncSession, run_id: int) -> list[LoadTestMetric]:
        result = await db.execute(
            select(LoadTestMetric)
            .where(LoadTestMetric.run_id == run_id)
            .order_by(LoadTestMetric.timestamp)
        )
        return list(result.scalars().all())

    async def simulate_run(self, db: AsyncSession, run_id: int) -> LoadTestRun:
        """Simulate a load test run with synthetic metrics."""
        run = await self.get_run(db, run_id)
        if not run:
            raise ValueError("Run not found")

        run.status = "running"
        run.started_at = datetime.utcnow()
        await db.commit()

        profile = await self.get_profile(db, run.profile_id) if run.profile_id else None
        duration = profile.duration_seconds if profile else 60
        total_users = run.device_count + run.virtual_device_count

        # Generate synthetic metrics
        import math
        total_requests = 0
        total_errors = 0
        latencies = []

        for t in range(0, duration, 5):
            # Simulate ramp-up then steady state
            phase_progress = t / duration
            if phase_progress < 0.2:
                active = int(total_users * phase_progress / 0.2)
            elif phase_progress < 0.8:
                active = total_users
            else:
                active = int(total_users * (1 - phase_progress) / 0.2)

            active = max(1, active)
            rps = active * random.uniform(0.8, 1.2)
            avg_lat = random.uniform(20, 100) + (active / total_users) * 50
            p99_lat = avg_lat * random.uniform(2, 4)
            err_rate = random.uniform(0, 0.05) + (0.01 if active > total_users * 0.8 else 0)

            requests_in_interval = int(rps * 5)
            errors_in_interval = int(requests_in_interval * err_rate)
            total_requests += requests_in_interval
            total_errors += errors_in_interval
            latencies.append(avg_lat)

            metric = LoadTestMetric(
                run_id=run_id,
                timestamp=datetime.utcnow(),
                rps=round(rps, 1),
                avg_latency_ms=round(avg_lat, 1),
                p99_latency_ms=round(p99_lat, 1),
                error_rate=round(err_rate * 100, 2),
                active_users=active,
            )
            db.add(metric)

        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.total_requests = total_requests
        run.error_count = total_errors
        run.avg_latency_ms = round(sum(latencies) / len(latencies), 1) if latencies else 0
        run.p99_latency_ms = round(run.avg_latency_ms * 3, 1)

        await db.commit()
        await db.refresh(run)
        return run


load_test_service = LoadTestService()
