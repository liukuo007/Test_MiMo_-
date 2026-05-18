from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Callable, Optional

import structlog
import paho.mqtt.client as mqtt

from simulator.config import config

logger = structlog.get_logger()


class MQTTHandler:
    """Real paho-mqtt handler connecting to Mosquitto broker."""

    def __init__(self, broker_url: str = ""):
        self.broker_url = broker_url or config.MQTT_BROKER_URL
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)
        self._message_log: list[dict] = []

    def connect(self):
        self._client = mqtt.Client(client_id=f"iot-simulator-{int(time.time())}", protocol=mqtt.MQTTv311)

        url = self.broker_url.replace("mqtt://", "")
        host, port = url.split(":") if ":" in url else (url, 1883)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect(host, int(port), keepalive=60)
            self._client.loop_start()
            logger.info("mqtt_connecting", broker=self.broker_url)
        except Exception as e:
            logger.warning("mqtt_connect_failed", error=str(e))

    @property
    def is_connected(self) -> bool:
        return self._connected

    def publish(self, topic: str, payload: dict):
        if not self._client or not self._connected:
            return
        message = json.dumps(payload)
        result = self._client.publish(topic, message, qos=1)
        self._message_log.append({"topic": topic, "payload": payload, "timestamp": time.time()})
        logger.debug("mqtt_publish", topic=topic)

    def subscribe(self, topic: str, callback: Callable):
        self._subscriptions[topic].append(callback)
        if self._client and self._connected:
            self._client.subscribe(topic, qos=1)
        logger.info("mqtt_subscribed", topic=topic)

    def unsubscribe(self, topic: str):
        self._subscriptions.pop(topic, None)
        if self._client and self._connected:
            self._client.unsubscribe(topic)

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            self._subscriptions.clear()
            logger.info("mqtt_disconnected")

    def get_message_count(self) -> int:
        return len(self._message_log)

    def get_messages(self, topic: Optional[str] = None) -> list[dict]:
        if topic:
            return [m for m in self._message_log if m["topic"] == topic]
        return list(self._message_log)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("mqtt_connected", broker=self.broker_url)
            for topic in self._subscriptions:
                client.subscribe(topic, qos=1)
        else:
            logger.error("mqtt_connect_error", rc=rc)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("mqtt_unexpected_disconnect", rc=rc)

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            payload = {"raw": msg.payload.decode()}

        self._message_log.append({"topic": topic, "payload": payload, "timestamp": time.time()})

        for pattern, callbacks in self._subscriptions.items():
            if mqtt.topic_matches_sub(pattern, topic):
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as e:
                        logger.error("mqtt_callback_error", topic=topic, error=str(e))
