from enum import Enum


class DeviceState(str, Enum):
    IDLE = "idle"
    DOOR_OPEN = "door_open"
    ITEM_DETECTING = "item_detecting"
    AI_RECOGNIZING = "ai_recognizing"
    ORDER_CREATING = "order_creating"
    PAYMENT_PROCESSING = "payment_processing"
    ERROR = "error"


TRANSITIONS = {
    ("idle", "door_open_cmd"): "door_open",
    ("door_open", "item_detected"): "item_detecting",
    ("item_detecting", "ai_result"): "ai_recognizing",
    ("ai_recognizing", "door_close_cmd"): "order_creating",
    ("order_creating", "payment_result"): "payment_processing",
    ("payment_processing", "payment_success"): "idle",
    ("door_open", "timeout"): "error",
    ("item_detecting", "timeout"): "error",
    ("ai_recognizing", "timeout"): "error",
    ("order_creating", "timeout"): "error",
    ("payment_processing", "payment_failed"): "error",
    ("error", "reset"): "idle",
    ("error", "door_close_cmd"): "idle",
    ("idle", "fault_inject"): "error",
}


class DeviceStateMachine:
    def __init__(self):
        self.state = DeviceState.IDLE
        self.history: list[tuple[str, DeviceState]] = []

    def transition(self, event: str) -> DeviceState:
        key = (self.state.value, event)
        prev_state = self.state
        if key in TRANSITIONS:
            self.state = DeviceState(TRANSITIONS[key])
            self.history.append((event, self.state))
        return self.state

    def reset(self):
        self.state = DeviceState.IDLE
        self.history.clear()

    def can_transition(self, event: str) -> bool:
        return (self.state.value, event) in TRANSITIONS
