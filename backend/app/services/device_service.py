from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DeviceOccupiedError, NotFoundError
from app.models.device import Device, DeviceStatus, DeviceType


class DeviceService:
    async def occupy(self, db: AsyncSession, device_id: int, user_id: int) -> Device:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise NotFoundError("Device", device_id)
        if device.status == DeviceStatus.OCCUPIED and device.occupied_by != user_id:
            raise DeviceOccupiedError(device.device_sn)

        device.status = DeviceStatus.OCCUPIED
        device.occupied_by = user_id
        await db.flush()
        return device

    async def release(self, db: AsyncSession, device_id: int) -> Device:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise NotFoundError("Device", device_id)

        device.status = DeviceStatus.ONLINE
        device.occupied_by = None
        await db.flush()
        return device

    async def create_virtual_batch(
        self, db: AsyncSession, count: int, device_type: DeviceType, region: str, project_id: int | None
    ) -> list[Device]:
        devices = []
        for i in range(count):
            device = Device(
                name=f"virtual-{device_type.value}-{i+1:04d}",
                device_sn=f"VIR-{region.upper()}-{i+1:08d}",
                device_type=device_type,
                status=DeviceStatus.ONLINE,
                region=region,
                project_id=project_id,
            )
            db.add(device)
            devices.append(device)
        await db.flush()
        return devices


device_service = DeviceService()
