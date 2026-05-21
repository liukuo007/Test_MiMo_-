import asyncio

from app.iot.device_state import DeviceEvent
from app.iot.fault_injector import FaultConfig, FaultInjector, FaultType
from app.iot.virtual_device import VirtualDevice


async def run_chaos_scenario(device: VirtualDevice, fault_type: FaultType) -> dict:
    """混沌场景：注入故障后验证设备恢复能力"""
    injector = FaultInjector()

    await device.send_event(DeviceEvent.DOOR_OPEN_CMD)
    await asyncio.sleep(0.2)

    config = FaultConfig(fault_type=fault_type, severity=0.7, duration_seconds=5)
    fault_result = await injector.inject(device.device_sn, config)

    await asyncio.sleep(1)
    await device.send_event(DeviceEvent.RESET)
    await asyncio.sleep(0.5)

    recovered = device.state_machine.state.value == "idle"

    return {
        "fault_type": fault_type.value,
        "fault_result": fault_result,
        "recovered": recovered,
        "final_state": device.state_machine.state.value,
    }
