from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.iot.device_state import DeviceEvent, DeviceState, DeviceStateMachine


@dataclass
class VirtualDevice:
    device_sn: str
    region: str = "cn"
    state_machine: DeviceStateMachine = field(default_factory=DeviceStateMachine)
    temperature: float = 25.0
    is_online: bool = True
    last_heartbeat: float = field(default_factory=time.time)
    events: list[dict] = field(default_factory=list)

    async def send_event(self, event: DeviceEvent, params: Optional[dict] = None) -> DeviceState:
        old_state = self.state_machine.state
        new_state = self.state_machine.transition(event)
        self.events.append({
            "timestamp": time.time(),
            "event": event.value,
            "from": old_state.value,
            "to": new_state.value,
            "params": params,
        })
        return new_state

    def get_status(self) -> dict:
        return {
            "device_sn": self.device_sn,
            "state": self.state_machine.state.value,
            "temperature": self.temperature,
            "is_online": self.is_online,
            "last_heartbeat": self.last_heartbeat,
            "event_count": len(self.events),
        }


class VirtualDeviceManager:
    def __init__(self):
        self._devices: dict[str, VirtualDevice] = {}

    def create(self, region: str = "cn") -> VirtualDevice:
        sn = f"VIR-{region.upper()}-{uuid.uuid4().hex[:8].upper()}"
        device = VirtualDevice(device_sn=sn, region=region)
        self._devices[sn] = device
        return device

    def get(self, device_sn: str) -> Optional[VirtualDevice]:
        return self._devices.get(device_sn)

    def remove(self, device_sn: str):
        self._devices.pop(device_sn, None)

    def list_all(self) -> list[VirtualDevice]:
        return list(self._devices.values())

    async def cleanup(self):
        self._devices.clear()


virtual_device_manager = VirtualDeviceManager()
