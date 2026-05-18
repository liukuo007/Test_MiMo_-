from __future__ import annotations

import os


class Config:
    MQTT_BROKER_URL: str = os.getenv("MQTT_BROKER_URL", "mqtt://localhost:1883")
    MIMO_API_URL: str = os.getenv("MIMO_API_URL", "http://localhost:8100/api/v1")
    DEVICE_COUNT: int = int(os.getenv("DEVICE_COUNT", "10"))
    REGION: str = os.getenv("REGION", "cn")
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
