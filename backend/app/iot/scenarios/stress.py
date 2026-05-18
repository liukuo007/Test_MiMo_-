import asyncio
import time

from app.iot.virtual_device import VirtualDevice, VirtualDeviceManager


async def run_stress_test(device_count: int, duration_seconds: int) -> dict:
    """压力测试：大量虚拟设备同时执行业务流程"""
    manager = VirtualDeviceManager()
    devices = [manager.create() for _ in range(device_count)]

    start = time.time()
    total_operations = 0
    errors = 0

    async def device_loop(device: VirtualDevice):
        nonlocal total_operations, errors
        while time.time() - start < duration_seconds:
            try:
                from app.iot.scenarios.normal import run_normal_flow
                await run_normal_flow(device)
                total_operations += 1
            except Exception:
                errors += 1
            await asyncio.sleep(0.1)

    await asyncio.gather(*[device_loop(d) for d in devices], return_exceptions=True)

    actual_duration = time.time() - start
    return {
        "device_count": device_count,
        "duration_seconds": round(actual_duration, 2),
        "total_operations": total_operations,
        "errors": errors,
        "ops_per_second": round(total_operations / actual_duration, 2),
        "error_rate": round(errors / max(total_operations + errors, 1) * 100, 2),
    }
