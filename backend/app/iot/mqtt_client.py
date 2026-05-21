from __future__ import annotations

import json
from collections.abc import Callable

import paho.mqtt.client as mqtt
import structlog

from app.config import get_settings

logger = structlog.get_logger()


class MQTTClient:
    """paho-mqtt wrapper for device communication."""

    def __init__(self):
        self._client: mqtt.Client | None = None
        self._connected = False
        self._subscriptions: dict[str, list[Callable]] = {}

    def connect(self):
        settings = get_settings()
        self._client = mqtt.Client(client_id="mimo-backend", protocol=mqtt.MQTTv311)

        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # Parse broker URL: mqtt://host:port
        url = settings.mqtt_broker_url.replace("mqtt://", "")
        host, port = url.split(":") if ":" in url else (url, 1883)

        try:
            self._client.connect(host, int(port), keepalive=60)
            self._client.loop_start()
            logger.info("mqtt_connecting", host=host, port=port)
        except Exception as e:
            logger.warning("mqtt_connect_failed", error=str(e))

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("mqtt_disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def publish_command(self, device_sn: str, command: str, payload: dict):
        """下发设备指令"""
        topic = f"device/{device_sn}/command"
        message = json.dumps({
            "command": command,
            "payload": payload,
        })
        if self._client and self._connected:
            result = self._client.publish(topic, message, qos=1)
            logger.info("mqtt_command_sent", device_sn=device_sn, command=command, mid=result.mid)
            return result
        else:
            logger.warning("mqtt_not_connected", device_sn=device_sn, command=command)
            return None

    def subscribe_heartbeat(self, device_sn: str, callback: Callable):
        """订阅设备心跳"""
        topic = f"device/{device_sn}/heartbeat"
        self._subscribe(topic, callback)

    def subscribe_event(self, device_sn: str, callback: Callable):
        """订阅设备事件"""
        topic = f"device/{device_sn}/event"
        self._subscribe(topic, callback)

    def subscribe_all_heartbeats(self, callback: Callable):
        """订阅所有设备心跳"""
        self._subscribe("device/+/heartbeat", callback)

    def subscribe_all_events(self, callback: Callable):
        """订阅所有设备事件"""
        self._subscribe("device/+/event", callback)

    def _subscribe(self, topic: str, callback: Callable):
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
            if self._client and self._connected:
                self._client.subscribe(topic, qos=1)
        self._subscriptions[topic].append(callback)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("mqtt_connected")
            # Re-subscribe on reconnect
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

        # Find matching subscriptions (support wildcards)
        for pattern, callbacks in self._subscriptions.items():
            if mqtt.topic_matches_sub(pattern, topic):
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as e:
                        logger.error("mqtt_callback_error", topic=topic, error=str(e))


mqtt_client = MQTTClient()
