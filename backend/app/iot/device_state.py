from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DeviceState(str, Enum):
    IDLE = "idle"
    DOOR_OPENING = "door_opening"
    DOOR_OPEN = "door_open"
    ITEM_DETECTING = "item_detecting"
    AI_RECOGNIZING = "ai_recognizing"
    DOOR_CLOSING = "door_closing"
    ORDER_CREATING = "order_creating"
    PAYMENT_PROCESSING = "payment_processing"
    ERROR = "error"


class DeviceEvent(str, Enum):
    DOOR_OPEN_CMD = "door_open_cmd"
    DOOR_CLOSE_CMD = "door_close_cmd"
    ITEM_DETECTED = "item_detected"
    AI_RESULT = "ai_result"
    PAYMENT_RESULT = "payment_result"
    ERROR_OCCURRED = "error_occurred"
    RESET = "reset"


# 状态转移表
TRANSITIONS: dict[tuple[DeviceState, DeviceEvent], DeviceState] = {
    (DeviceState.IDLE, DeviceEvent.DOOR_OPEN_CMD): DeviceState.DOOR_OPENING,
    (DeviceState.DOOR_OPENING, DeviceEvent.DOOR_OPEN_CMD): DeviceState.DOOR_OPEN,
    (DeviceState.DOOR_OPEN, DeviceEvent.ITEM_DETECTED): DeviceState.ITEM_DETECTING,
    (DeviceState.ITEM_DETECTING, DeviceEvent.AI_RESULT): DeviceState.AI_RECOGNIZING,
    (DeviceState.AI_RECOGNIZING, DeviceEvent.DOOR_CLOSE_CMD): DeviceState.DOOR_CLOSING,
    (DeviceState.DOOR_CLOSING, DeviceEvent.DOOR_CLOSE_CMD): DeviceState.ORDER_CREATING,
    (DeviceState.ORDER_CREATING, DeviceEvent.PAYMENT_RESULT): DeviceState.PAYMENT_PROCESSING,
    (DeviceState.PAYMENT_PROCESSING, DeviceEvent.PAYMENT_RESULT): DeviceState.IDLE,
}

# 任意状态都可以通过 RESET 回到 IDLE
for state in DeviceState:
    TRANSITIONS[(state, DeviceEvent.RESET)] = DeviceState.IDLE
    TRANSITIONS[(state, DeviceEvent.ERROR_OCCURRED)] = DeviceState.ERROR


@dataclass
class DeviceStateMachine:
    state: DeviceState = DeviceState.IDLE
    history: list[dict] = field(default_factory=list)

    def transition(self, event: DeviceEvent) -> DeviceState:
        key = (self.state, event)
        if key in TRANSITIONS:
            old_state = self.state
            self.state = TRANSITIONS[key]
            self.history.append({
                "from": old_state.value,
                "event": event.value,
                "to": self.state.value,
            })
        return self.state
