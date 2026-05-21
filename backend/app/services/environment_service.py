from __future__ import annotations

import asyncio
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.environment import Environment, EnvironmentHealthCheck, EnvironmentSnapshot


class EnvironmentService:

    async def list_environments(
        self, db: AsyncSession, env_type: Optional[str] = None, status: Optional[str] = None
    ) -> list[Environment]:
        q = select(Environment).order_by(Environment.id)
        if env_type:
            q = q.where(Environment.env_type == env_type)
        if status:
            q = q.where(Environment.status == status)
        result = await db.execute(q)
        return list(result.scalars().all())

    async def get_environment(self, db: AsyncSession, env_id: int) -> Optional[Environment]:
        result = await db.execute(
            select(Environment)
            .where(Environment.id == env_id)
            .options(selectinload(Environment.snapshots), selectinload(Environment.health_checks))
        )
        return result.scalar_one_or_none()

    async def create_environment(self, db: AsyncSession, data: dict) -> Environment:
        env = Environment(**data)
        db.add(env)
        await db.commit()
        await db.refresh(env)
        return env

    async def update_environment(self, db: AsyncSession, env_id: int, data: dict) -> Optional[Environment]:
        env = await self.get_environment(db, env_id)
        if not env:
            return None
        for k, v in data.items():
            if v is not None and hasattr(env, k):
                setattr(env, k, v)
        await db.commit()
        await db.refresh(env)
        return env

    async def delete_environment(self, db: AsyncSession, env_id: int) -> bool:
        env = await self.get_environment(db, env_id)
        if not env:
            return False
        await db.delete(env)
        await db.commit()
        return True

    async def check_health(self, db: AsyncSession, env_id: int) -> list[EnvironmentHealthCheck]:
        env = await self.get_environment(db, env_id)
        if not env:
            return []

        checks = []
        components = [
            ("redis", env.redis_url),
            ("postgres", env.db_url),
            ("mqtt", env.mqtt_broker_url),
            ("wiremock", env.wiremock_url),
            ("ai", env.ai_evaluator_url),
            ("payment", env.payment_endpoint),
        ]

        for comp_name, url in components:
            if not url:
                continue
            status, latency, details = await self._probe_component(comp_name, url)
            check = EnvironmentHealthCheck(
                env_id=env_id,
                component=comp_name,
                status=status,
                latency_ms=latency,
                details=details,
            )
            db.add(check)
            checks.append(check)

        # Update overall environment status
        if checks:
            statuses = [c.status for c in checks]
            if all(s == "healthy" for s in statuses):
                env.status = "healthy"
            elif any(s == "down" for s in statuses):
                env.status = "down"
            else:
                env.status = "degraded"
        else:
            env.status = "unknown"

        await db.commit()
        return checks

    async def _probe_component(self, component: str, url: str) -> tuple[str, float, dict]:
        start = time.monotonic()
        try:
            if component == "redis":
                return await self._probe_redis(url, start)
            elif component == "postgres":
                return await self._probe_postgres(url, start)
            elif component == "mqtt":
                return await self._probe_mqtt(url, start)
            else:
                return await self._probe_http(url, start)
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return "down", round(latency, 2), {"error": str(e)}

    async def _probe_redis(self, url: str, start: float) -> tuple[str, float, dict]:
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(url)
            await r.ping()
            await r.aclose()
            latency = (time.monotonic() - start) * 1000
            return "healthy", round(latency, 2), {"message": "pong"}
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return "down", round(latency, 2), {"error": str(e)}

    async def _probe_postgres(self, url: str, start: float) -> tuple[str, float, dict]:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            engine = create_async_engine(url, pool_size=1)
            async with engine.connect() as conn:
                await conn.execute(select(1))
            await engine.dispose()
            latency = (time.monotonic() - start) * 1000
            return "healthy", round(latency, 2), {"message": "connected"}
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return "down", round(latency, 2), {"error": str(e)}

    async def _probe_mqtt(self, url: str, start: float) -> tuple[str, float, dict]:
        try:
            import paho.mqtt.client as mqtt
            connected = asyncio.Event()
            loop = asyncio.get_event_loop()

            def on_connect(client, userdata, flags, rc):
                loop.call_soon_threadsafe(connected.set)

            client = mqtt.Client()
            client.on_connect = on_connect
            parts = url.replace("mqtt://", "").split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 1883
            client.connect_async(host, port, 10)
            client.loop_start()
            try:
                await asyncio.wait_for(connected.wait(), timeout=5)
                latency = (time.monotonic() - start) * 1000
                return "healthy", round(latency, 2), {"message": "connected"}
            finally:
                client.loop_stop()
                client.disconnect()
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return "down", round(latency, 2), {"error": str(e)}

    async def _probe_http(self, url: str, start: float) -> tuple[str, float, dict]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
            latency = (time.monotonic() - start) * 1000
            if resp.status_code < 400:
                return "healthy", round(latency, 2), {"status_code": resp.status_code}
            return "degraded", round(latency, 2), {"status_code": resp.status_code}
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return "down", round(latency, 2), {"error": str(e)}

    async def create_snapshot(
        self, db: AsyncSession, env_id: int, name: str, snapshot_type: str = "manual", notes: Optional[str] = None
    ) -> Optional[EnvironmentSnapshot]:
        env = await self.get_environment(db, env_id)
        if not env:
            return None
        snapshot = EnvironmentSnapshot(
            env_id=env_id,
            name=name,
            snapshot_type=snapshot_type,
            state_data={
                "base_url": env.base_url,
                "mqtt_broker_url": env.mqtt_broker_url,
                "db_url": env.db_url,
                "redis_url": env.redis_url,
                "ai_evaluator_url": env.ai_evaluator_url,
                "wiremock_url": env.wiremock_url,
                "payment_endpoint": env.payment_endpoint,
                "config": env.config,
            },
            notes=notes,
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    async def restore_snapshot(self, db: AsyncSession, snapshot_id: int) -> Optional[Environment]:
        result = await db.execute(
            select(EnvironmentSnapshot).where(EnvironmentSnapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot or not snapshot.state_data:
            return None

        env_result = await db.execute(
            select(Environment).where(Environment.id == snapshot.env_id)
        )
        env = env_result.scalar_one_or_none()
        if not env:
            return None

        for k, v in snapshot.state_data.items():
            if hasattr(env, k):
                setattr(env, k, v)
        await db.commit()
        await db.refresh(env)
        return env

    async def list_snapshots(self, db: AsyncSession, env_id: int) -> list[EnvironmentSnapshot]:
        result = await db.execute(
            select(EnvironmentSnapshot)
            .where(EnvironmentSnapshot.env_id == env_id)
            .order_by(EnvironmentSnapshot.created_at.desc())
        )
        return list(result.scalars().all())


environment_service = EnvironmentService()
