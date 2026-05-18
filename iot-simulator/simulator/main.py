from __future__ import annotations

import asyncio

import structlog

from simulator.config import config
from simulator.device import VirtualDeviceManager
from simulator.mqtt_handler import MQTTHandler
from simulator.api_client import api_client
from simulator.scenarios.normal_flow import run_normal_flow
from simulator.scenarios.fault_injection import inject_fault

logger = structlog.get_logger()


async def main():
    logger.info("iot_simulator_started", mqtt_broker=config.MQTT_BROKER_URL, api_url=config.MIMO_API_URL,
                device_count=config.DEVICE_COUNT, region=config.REGION)

    mqtt = MQTTHandler()
    mqtt.connect()

    # Wait for MQTT connection
    for _ in range(10):
        if mqtt.is_connected:
            break
        await asyncio.sleep(0.5)

    manager = VirtualDeviceManager(mqtt_handler=mqtt)
    devices = manager.create_batch(count=config.DEVICE_COUNT, region=config.REGION)
    logger.info("virtual_devices_created", count=len(devices))

    # Register devices with backend
    for device in devices:
        await api_client.register_device(
            device_sn=device.device_sn,
            name=f"sim-{device.device_sn}",
            device_type="virtual_l2",
            region=device.region,
        )
    logger.info("devices_registered", count=len(devices))

    # Run normal flow demo
    demo_device = devices[0]
    logger.info("running_normal_flow_demo", device_sn=demo_device.device_sn)
    result = await run_normal_flow(demo_device, mqtt)
    logger.info("normal_flow_result", **result)

    # Run fault injection demo
    if len(devices) > 1:
        logger.info("running_fault_injection_demo", device_sn=devices[1].device_sn)
        fault_result = await inject_fault(devices[1], "network_latency", duration=3)
        logger.info("fault_injection_result", status=fault_result["status"],
                     recovered=fault_result["system_recovered"])

    # Start heartbeat loops for remaining devices
    logger.info("starting_heartbeat_loops")
    tasks = [device.run() for device in devices[2:]]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("iot_simulator_stopping")
    finally:
        manager.stop_all()
        mqtt.disconnect()
        logger.info("iot_simulator_stopped", messages_sent=mqtt.get_message_count())


if __name__ == "__main__":
    asyncio.run(main())
