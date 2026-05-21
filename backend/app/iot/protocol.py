from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MessageType(str, Enum):
    HEARTBEAT = "heartbeat"
    DOOR_CMD = "door_cmd"
    STATUS_REPORT = "status_report"
    ITEM_EVENT = "item_event"
    AI_RESULT = "ai_result"
    ORDER_CMD = "order_cmd"
    PAYMENT_RESULT = "payment_result"
    FIRMWARE_OTA = "firmware_ota"
    ERROR = "error"


@dataclass
class IoTMessage:
    message_type: MessageType
    device_sn: str
    payload: dict
    timestamp: Optional[float] = None
    message_id: Optional[str] = None

    def to_mqtt_payload(self) -> bytes:
        return json.dumps({
            "type": self.message_type.value,
            "device_sn": self.device_sn,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
        }).encode()

    @classmethod
    def from_mqtt_payload(cls, payload: bytes) -> IoTMessage:
        data = json.loads(payload)
        return cls(
            message_type=MessageType(data["type"]),
            device_sn=data["device_sn"],
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp"),
            message_id=data.get("message_id"),
        )

    @staticmethod
    def topic(device_sn: str, msg_type: MessageType) -> str:
        return f"device/{device_sn}/{msg_type.value}"
