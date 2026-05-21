from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.device import Device, DeviceStatus
from app.models.device_pool import DeviceHealthScore, DevicePool, DevicePoolMember, DeviceTag
from app.models.test_result import TestResult


class DeviceMeshService:

    # --- Pool CRUD ---
    async def list_pools(self, db: AsyncSession) -> list[DevicePool]:
        result = await db.execute(
            select(DevicePool).options(selectinload(DevicePool.members)).order_by(DevicePool.id)
        )
        return list(result.scalars().all())

    async def get_pool(self, db: AsyncSession, pool_id: int) -> DevicePool | None:
        result = await db.execute(
            select(DevicePool)
            .where(DevicePool.id == pool_id)
            .options(selectinload(DevicePool.members))
        )
        return result.scalar_one_or_none()

    async def create_pool(self, db: AsyncSession, data: dict) -> DevicePool:
        pool = DevicePool(**data)
        db.add(pool)
        await db.commit()
        await db.refresh(pool)
        return pool

    async def update_pool(self, db: AsyncSession, pool_id: int, data: dict) -> DevicePool | None:
        pool = await self.get_pool(db, pool_id)
        if not pool:
            return None
        for k, v in data.items():
            if v is not None and hasattr(pool, k):
                setattr(pool, k, v)
        await db.commit()
        await db.refresh(pool)
        return pool

    async def delete_pool(self, db: AsyncSession, pool_id: int) -> bool:
        pool = await self.get_pool(db, pool_id)
        if not pool:
            return False
        await db.delete(pool)
        await db.commit()
        return True

    # --- Members ---
    async def assign_devices(self, db: AsyncSession, pool_id: int, device_ids: list[int]) -> list[DevicePoolMember]:
        members = []
        for did in device_ids:
            exists = await db.execute(
                select(DevicePoolMember).where(
                    DevicePoolMember.pool_id == pool_id, DevicePoolMember.device_id == did
                )
            )
            if exists.scalar_one_or_none():
                continue
            m = DevicePoolMember(pool_id=pool_id, device_id=did)
            db.add(m)
            members.append(m)
        await db.commit()
        return members

    async def remove_device(self, db: AsyncSession, pool_id: int, device_id: int) -> bool:
        result = await db.execute(
            select(DevicePoolMember).where(
                DevicePoolMember.pool_id == pool_id, DevicePoolMember.device_id == device_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await db.delete(member)
        await db.commit()
        return True

    async def get_pool_devices(self, db: AsyncSession, pool_id: int) -> list[dict]:
        result = await db.execute(
            select(DevicePoolMember, Device)
            .join(Device, DevicePoolMember.device_id == Device.id)
            .where(DevicePoolMember.pool_id == pool_id)
        )
        devices = []
        for member, device in result.all():
            devices.append({
                "member_id": member.id,
                "device_id": device.id,
                "name": device.name,
                "sn": device.device_sn,
                "status": device.status.value if hasattr(device.status, 'value') else device.status,
                "device_type": device.device_type.value if hasattr(device.device_type, 'value') else device.device_type,
                "added_at": member.added_at,
            })
        return devices

    # --- Tags ---
    async def add_tags(self, db: AsyncSession, device_id: int, tags: list[dict]) -> list[DeviceTag]:
        result = []
        for t in tags:
            tag = DeviceTag(device_id=device_id, tag_key=t["tag_key"], tag_value=t["tag_value"])
            db.add(tag)
            result.append(tag)
        await db.commit()
        return result

    async def get_device_tags(self, db: AsyncSession, device_id: int) -> list[DeviceTag]:
        result = await db.execute(
            select(DeviceTag).where(DeviceTag.device_id == device_id)
        )
        return list(result.scalars().all())

    async def get_devices_by_tags(self, db: AsyncSession, tags: dict[str, str]) -> list[int]:
        """Get device IDs matching ALL specified tag key-value pairs."""
        device_ids = None
        for key, value in tags.items():
            result = await db.execute(
                select(DeviceTag.device_id).where(
                    DeviceTag.tag_key == key, DeviceTag.tag_value == value
                )
            )
            ids = set(result.scalars().all())
            if device_ids is None:
                device_ids = ids
            else:
                device_ids &= ids
        return list(device_ids) if device_ids else []

    async def remove_tag(self, db: AsyncSession, tag_id: int) -> bool:
        result = await db.execute(select(DeviceTag).where(DeviceTag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            return False
        await db.delete(tag)
        await db.commit()
        return True

    # --- Health Score ---
    async def compute_health_score(self, db: AsyncSession, device_id: int) -> DeviceHealthScore:
        device_result = await db.execute(select(Device).where(Device.id == device_id))
        device = device_result.scalar_one_or_none()

        factors = {}
        score = 100.0

        if device:
            # Factor 1: Online status
            if device.status == DeviceStatus.ONLINE:
                factors["online"] = 100
            elif device.status == DeviceStatus.OCCUPIED:
                factors["online"] = 80
            else:
                factors["online"] = 0
                score -= 30

            # Factor 2: Heartbeat freshness
            if device.last_heartbeat:
                from datetime import datetime
                age = (datetime.utcnow() - device.last_heartbeat).total_seconds()
                if age < 60:
                    factors["heartbeat"] = 100
                elif age < 300:
                    factors["heartbeat"] = 70
                    score -= 10
                else:
                    factors["heartbeat"] = 30
                    score -= 25
            else:
                factors["heartbeat"] = 0
                score -= 20

            # Factor 3: Temperature
            if device.temperature is not None:
                if device.temperature < 45:
                    factors["temperature"] = 100
                elif device.temperature < 60:
                    factors["temperature"] = 70
                    score -= 10
                else:
                    factors["temperature"] = 30
                    score -= 20

            # Factor 4: Recent error rate (TestResult uses device_sn, not device_id)
            device_sn = device.device_sn
            result_count = await db.execute(
                select(func.count()).select_from(TestResult).where(
                    TestResult.device_sn == device_sn
                )
            )
            total = result_count.scalar() or 0
            if total > 0:
                fail_count = await db.execute(
                    select(func.count()).select_from(TestResult).where(
                        TestResult.device_sn == device_sn, TestResult.status == "failed"
                    )
                )
                fails = fail_count.scalar() or 0
                error_rate = fails / total
                factors["error_rate"] = round((1 - error_rate) * 100, 1)
                if error_rate > 0.3:
                    score -= 20
                elif error_rate > 0.1:
                    score -= 10
            else:
                factors["error_rate"] = 100

        score = max(0, min(100, score))

        # Upsert
        existing = await db.execute(
            select(DeviceHealthScore).where(DeviceHealthScore.device_id == device_id)
        )
        hs = existing.scalar_one_or_none()
        if hs:
            hs.score = score
            hs.factors = factors
        else:
            hs = DeviceHealthScore(device_id=device_id, score=score, factors=factors)
            db.add(hs)
        await db.commit()
        await db.refresh(hs)
        return hs

    # --- Scheduling ---
    async def auto_schedule(
        self, db: AsyncSession, pool_id: int, strategy: str = "least_busy", count: int = 1
    ) -> list[dict]:
        """Pick devices from pool based on strategy."""
        pool_devices = await self.get_pool_devices(db, pool_id)
        if not pool_devices:
            return []

        device_ids = [d["device_id"] for d in pool_devices]
        available = [d for d in pool_devices if d["status"] in ("online", "occupied")]
        if not available:
            return []

        if strategy == "least_busy":
            # Pick devices with fewest recent tasks
            scored = []
            for d in available:
                task_count = await db.execute(
                    select(func.count()).select_from(TestResult).where(
                        TestResult.device_sn == d["sn"]
                    )
                )
                scored.append((d, task_count.scalar() or 0))
            scored.sort(key=lambda x: x[1])
            return [s[0] for s in scored[:count]]

        elif strategy == "most_stable":
            # Pick devices with highest health score
            scored = []
            for d in available:
                hs_result = await db.execute(
                    select(DeviceHealthScore).where(DeviceHealthScore.device_id == d["device_id"])
                )
                hs = hs_result.scalar_one_or_none()
                scored.append((d, hs.score if hs else 50))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [s[0] for s in scored[:count]]

        else:  # least_recently_checked (default)
            return available[:count]


device_mesh_service = DeviceMeshService()
