from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class ResourcePool:
    name: str
    total: int
    available: int
    occupied: dict[int, str] = field(default_factory=dict)  # resource_id -> user


class ResourceManager:
    """资源调度管理器"""

    def __init__(self):
        self._pools: dict[str, ResourcePool] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def register_pool(self, name: str, total: int):
        self._pools[name] = ResourcePool(name=name, total=total, available=total)
        self._locks[name] = asyncio.Lock()

    async def acquire(self, pool_name: str, user_id: int, count: int = 1) -> list[int]:
        async with self._locks[pool_name]:
            pool = self._pools[pool_name]
            if pool.available < count:
                return []

            acquired = []
            for resource_id, occupant in list(pool.occupied.items()):
                if occupant == str(user_id):
                    acquired.append(resource_id)

            for resource_id in range(pool.total):
                if len(acquired) >= count:
                    break
                if resource_id not in pool.occupied:
                    pool.occupied[resource_id] = str(user_id)
                    pool.available -= 1
                    acquired.append(resource_id)

            return acquired

    async def release(self, pool_name: str, resource_ids: list[int]):
        async with self._locks[pool_name]:
            pool = self._pools[pool_name]
            for rid in resource_ids:
                if rid in pool.occupied:
                    del pool.occupied[rid]
                    pool.available += 1

    def get_status(self, pool_name: str) -> dict:
        pool = self._pools.get(pool_name)
        if not pool:
            return {}
        return {
            "name": pool.name,
            "total": pool.total,
            "available": pool.available,
            "occupied": pool.total - pool.available,
        }


resource_manager = ResourceManager()
