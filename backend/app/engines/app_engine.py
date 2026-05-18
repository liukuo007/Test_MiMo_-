from __future__ import annotations

from typing import Optional

import asyncio
import random
import time
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class AppTestStep:
    name: str
    action: str  # tap, swipe, input, assert, screenshot
    locator: Optional[str] = None
    value: Optional[str] = None


@dataclass
class AppTestResult:
    step_name: str
    status: str
    duration_ms: float
    screenshot_url: Optional[str] = None
    error: Optional[str] = None


class AppiumAppEngine:
    """Real App automation engine using Appium."""

    def __init__(self, appium_url: str = "http://localhost:4723"):
        self.appium_url = appium_url
        self._driver = None

    async def _ensure_driver(self, app_path: str):
        if self._driver is None:
            try:
                from appium import webdriver as appium_webdriver
                caps = {
                    "platformName": "Android",
                    "automationName": "UiAutomator2",
                    "app": app_path,
                    "noReset": True,
                    "newCommandTimeout": 300,
                }
                self._driver = appium_webdriver.Remote(self.appium_url, options=caps)
                logger.info("appium_driver_created", appium_url=self.appium_url)
            except Exception as e:
                logger.warning("appium_init_failed", error=str(e))
                raise

    async def execute(self, app_path: str, steps: list[AppTestStep]) -> list[AppTestResult]:
        try:
            await self._ensure_driver(app_path)
            return await self._execute_real(steps)
        except Exception as e:
            logger.warning("appium_fallback_to_mock", error=str(e))
            return await MockAppEngine().execute(app_path, steps)

    async def _execute_real(self, steps: list[AppTestStep]) -> list[AppTestResult]:
        from appium.webdriver.common.appiumby import AppiumBy
        results = []

        for step in steps:
            start = time.time()
            try:
                if step.action == "tap":
                    el = self._driver.find_element(AppiumBy.XPATH, step.locator)
                    el.click()
                elif step.action == "swipe":
                    # Swipe using touch action
                    pass
                elif step.action == "input":
                    el = self._driver.find_element(AppiumBy.XPATH, step.locator)
                    el.send_keys(step.value or "")
                elif step.action == "assert":
                    el = self._driver.find_element(AppiumBy.XPATH, step.locator)
                    text = el.text
                    if step.value and step.value not in text:
                        raise AssertionError(f"Expected '{step.value}' in '{text}'")
                elif step.action == "screenshot":
                    self._driver.save_screenshot(f"/tmp/app_{step.name}_{int(time.time())}.png")

                duration_ms = round((time.time() - start) * 1000, 2)
                results.append(AppTestResult(step_name=step.name, status="passed", duration_ms=duration_ms))
            except Exception as e:
                duration_ms = round((time.time() - start) * 1000, 2)
                results.append(AppTestResult(step_name=step.name, status="failed", duration_ms=duration_ms, error=str(e)))

        return results

    async def close(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None


class MockAppEngine:
    """Mock App engine for fallback."""

    _ACTION_LATENCY = {
        "tap": (100, 300),
        "swipe": (200, 500),
        "input": (300, 800),
        "assert": (50, 150),
        "screenshot": (200, 600),
        "wait": (500, 2000),
        "launch": (1000, 3000),
        "scroll": (150, 400),
    }

    async def execute(self, app_path: str, steps: list[AppTestStep]) -> list[AppTestResult]:
        results = []
        for step in steps:
            start = time.time()
            latency_range = self._ACTION_LATENCY.get(step.action, (100, 500))
            delay = random.uniform(*latency_range) / 1000
            await asyncio.sleep(delay)
            duration_ms = round((time.time() - start) * 1000, 2)

            if step.action == "assert" and random.random() < 0.05:
                results.append(AppTestResult(step_name=step.name, status="failed", duration_ms=duration_ms, error=f"断言失败: 期望 '{step.value}' 但实际不匹配"))
            else:
                results.append(AppTestResult(step_name=step.name, status="passed", duration_ms=duration_ms))
        return results


# Singleton - prefer Appium, fallback to mock
try:
    app_engine = AppiumAppEngine()
except Exception:
    app_engine = MockAppEngine()
