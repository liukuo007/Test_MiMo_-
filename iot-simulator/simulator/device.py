from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import structlog

from simulator.mqtt_handler import MQTTHandler
from simulator.state_machine import DeviceStateMachine, DeviceState
from simulator.api_client import api_client
from simulator.config import config

logger = structlog.get_logger()


@dataclass
class VirtualDevice:
    device_sn: str
    region: str = "cn"
    is_running: bool = False
    heartbeat_interval: int = config.HEARTBEAT_INTERVAL
    mqtt: Optional[MQTTHandler] = None
    state_machine: DeviceStateMachine = field(default_factory=DeviceStateMachine)
    temperature: float = 25.0

    async def run(self):
        self.is_running = True
        # Subscribe to command topic
        if self.mqtt:
            self.mqtt.subscribe(f"device/{self.device_sn}/command", self._handle_command)
        while self.is_running:
            await self._send_heartbeat()
            await asyncio.sleep(self.heartbeat_interval)

    async def _send_heartbeat(self):
        state = self.state_machine.state.value
        payload = {
            "device_sn": self.device_sn,
            "state": state,
            "temperature": self.temperature,
            "timestamp": time.time(),
            "region": self.region,
        }
        if self.mqtt:
            self.mqtt.publish(f"device/{self.device_sn}/heartbeat", payload)
        # Also report via API
        await api_client.report_heartbeat(self.device_sn, state, self.temperature)
        logger.debug("heartbeat", device_sn=self.device_sn, state=state)

    def _handle_command(self, topic: str, payload: dict):
        command = payload.get("command", "")
        logger.info("command_received", device_sn=self.device_sn, command=command)

        if command == "open_door":
            self.send_event_sync("open_door")
        elif command == "close_door":
            self.send_event_sync("close_door")
        elif command == "restart":
            self.state_machine = DeviceStateMachine()
            logger.info("device_restarted", device_sn=self.device_sn)

    def send_event_sync(self, event: str) -> DeviceState:
        prev_state = self.state_machine.state
        new_state = self.state_machine.transition(event)
        if new_state != prev_state:
            payload = {
                "device_sn": self.device_sn,
                "event": event,
                "from_state": prev_state.value,
                "to_state": new_state.value,
                "timestamp": time.time(),
            }
            if self.mqtt:
                self.mqtt.publish(f"device/{self.device_sn}/event", payload)
            logger.info("state_transition", device_sn=self.device_sn, device_event=event,
                        from_state=prev_state.value, to_state=new_state.value)
        return new_state

    async def send_event(self, event: str) -> DeviceState:
        new_state = self.send_event_sync(event)
        await api_client.report_event(self.device_sn, event, {
            "from_state": self.state_machine.state.value,
            "to_state": new_state.value,
        })
        return new_state

    def stop(self):
        self.is_running = False


class VirtualDeviceManager:
    def __init__(self, mqtt_handler: Optional[MQTTHandler] = None):
        self._devices: list[VirtualDevice] = []
        self._mqtt = mqtt_handler

    def create_batch(self, count: int, region: str = "cn") -> list[VirtualDevice]:
        devices = []
        for i in range(count):
            sn = f"VIR-{region.upper()}-{uuid.uuid4().hex[:8].upper()}"
            device = VirtualDevice(device_sn=sn, region=region, mqtt=self._mqtt)
            self._devices.append(device)
            devices.append(device)
        return devices

    def get_device(self, device_sn: str) -> Optional[VirtualDevice]:
        for d in self._devices:
            if d.device_sn == device_sn:
                return d
        return None

    def stop_all(self):
        for device in self._devices:
            device.stop()

    @property
    def device_count(self) -> int:
        return len(self._devices)
