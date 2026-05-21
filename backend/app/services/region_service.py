from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DeviceStatus
from app.models.health_score import HealthScoreSnapshot
from app.models.region import Region, RegionMetric


class RegionService:

    async def list_regions(self, db: AsyncSession) -> list[Region]:
        result = await db.execute(select(Region).order_by(Region.id))
        return list(result.scalars().all())

    async def get_region(self, db: AsyncSession, region_id: int) -> Region | None:
        result = await db.execute(select(Region).where(Region.id == region_id))
        return result.scalar_one_or_none()

    async def get_region_by_code(self, db: AsyncSession, code: str) -> Region | None:
        result = await db.execute(select(Region).where(Region.code == code))
        return result.scalar_one_or_none()

    async def create_region(self, db: AsyncSession, data: dict) -> Region:
        region = Region(**data)
        db.add(region)
        await db.commit()
        await db.refresh(region)
        return region

    async def update_region(self, db: AsyncSession, region_id: int, data: dict) -> Region | None:
        region = await self.get_region(db, region_id)
        if not region:
            return None
        for k, v in data.items():
            if v is not None and hasattr(region, k):
                setattr(region, k, v)
        await db.commit()
        await db.refresh(region)
        return region

    async def get_region_health(self, db: AsyncSession, code: str) -> dict:
        """Get health metrics for a specific region."""
        metrics = {}

        # Health score from snapshots (fallback to latest if no region-specific)
        hs_result = await db.execute(
            select(HealthScoreSnapshot.overall_score)
            .where(HealthScoreSnapshot.region == code)
            .order_by(desc(HealthScoreSnapshot.computed_at))
            .limit(1)
        )
        health_score = hs_result.scalar_one_or_none()
        if health_score is None:
            fallback = await db.execute(
                select(HealthScoreSnapshot.overall_score)
                .order_by(desc(HealthScoreSnapshot.computed_at))
                .limit(1)
            )
            health_score = fallback.scalar_one_or_none()
        if health_score is not None:
            metrics["health_score"] = health_score

        # Device online rate — use all devices (Device has no region column)
        total_dev = await db.execute(
            select(func.count()).select_from(Device)
        )
        total = total_dev.scalar() or 0
        if total > 0:
            online_dev = await db.execute(
                select(func.count()).select_from(Device).where(
                    Device.status.in_([DeviceStatus.ONLINE, DeviceStatus.OCCUPIED]),
                )
            )
            online = online_dev.scalar() or 0
            metrics["device_online_rate"] = round(online / total * 100, 1)
            metrics["device_count"] = total

        # Store metrics
        for name, value in metrics.items():
            metric = RegionMetric(region_code=code, metric_name=name, metric_value=value)
            db.add(metric)
        await db.commit()

        overall = metrics.get("health_score", 0)
        return {"metrics": metrics, "overall_score": overall}

    async def get_global_quality_map(self, db: AsyncSession) -> list[dict]:
        """Get quality data for all regions for the global map."""
        regions = await self.list_regions(db)

        # Get latest health score as fallback
        hs_result = await db.execute(
            select(HealthScoreSnapshot.overall_score)
            .order_by(desc(HealthScoreSnapshot.computed_at))
            .limit(1)
        )
        fallback_score = hs_result.scalar_one_or_none() or 0

        result = []
        for region in regions:
            # Read existing metrics for this region
            metric_result = await db.execute(
                select(RegionMetric.metric_name, RegionMetric.metric_value)
                .where(RegionMetric.region_code == region.code)
                .order_by(desc(RegionMetric.computed_at))
                .limit(10)
            )
            metrics = {row[0]: row[1] for row in metric_result.all()}
            overall = metrics.get("health_score", fallback_score)
            result.append({
                "code": region.code,
                "name": region.name,
                "status": region.status,
                "overall_score": overall,
                "metrics": metrics,
            })
        return result


region_service = RegionService()
