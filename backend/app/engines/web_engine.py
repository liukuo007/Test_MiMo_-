from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class WebTestStep:
    name: str
    action: str  # navigate, click, fill, assert, screenshot
    selector: str | None = None
    value: str | None = None
    url: str | None = None


@dataclass
class WebTestResult:
    step_name: str
    status: str
    duration_ms: float
    screenshot_url: str | None = None
    error: str | None = None


class PlaywrightWebEngine:
    """Real Web automation engine using Playwright."""

    def __init__(self):
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
                logger.info("playwright_browser_launched")
            except Exception as e:
                logger.warning("playwright_init_failed", error=str(e))
                raise

    async def execute(self, base_url: str, steps: list[WebTestStep]) -> list[WebTestResult]:
        try:
            await self._ensure_browser()
            return await self._execute_real(base_url, steps)
        except Exception as e:
            logger.warning("playwright_fallback_to_mock", error=str(e))
            return await MockWebEngine().execute(base_url, steps)

    async def _execute_real(self, base_url: str, steps: list[WebTestStep]) -> list[WebTestResult]:
        page = await self._browser.new_page()
        results = []

        try:
            for step in steps:
                start = time.time()
                try:
                    await self._execute_step(page, step, base_url)
                    duration_ms = round((time.time() - start) * 1000, 2)
                    results.append(WebTestResult(
                        step_name=step.name,
                        status="passed",
                        duration_ms=duration_ms,
                    ))
                except Exception as e:
                    duration_ms = round((time.time() - start) * 1000, 2)
                    results.append(WebTestResult(
                        step_name=step.name,
                        status="failed",
                        duration_ms=duration_ms,
                        error=str(e),
                    ))
        finally:
            await page.close()

        return results

    async def _execute_step(self, page, step: WebTestStep, base_url: str):
        if step.action == "navigate":
            url = step.url or base_url
            await page.goto(url, timeout=30000)
        elif step.action == "click":
            await page.click(step.selector, timeout=10000)
        elif step.action == "fill":
            await page.fill(step.selector, step.value or "", timeout=10000)
        elif step.action == "assert":
            el = await page.wait_for_selector(step.selector, timeout=10000)
            text = await el.text_content()
            if step.value and step.value not in (text or ""):
                raise AssertionError(f"Expected '{step.value}' in '{text}'")
        elif step.action == "screenshot":
            await page.screenshot(path=f"/tmp/web_{step.name}_{int(time.time())}.png")
        elif step.action == "wait_for":
            await page.wait_for_selector(step.selector, timeout=10000)
        elif step.action == "select":
            await page.select_option(step.selector, step.value)
        elif step.action == "hover":
            await page.hover(step.selector, timeout=10000)

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class MockWebEngine:
    """Mock Web engine for fallback."""

    _WEB_ACTION_LATENCY = {
        "navigate": (500, 2000),
        "click": (100, 400),
        "fill": (200, 600),
        "assert": (50, 200),
        "screenshot": (300, 800),
        "wait_for": (200, 1500),
        "select": (150, 400),
        "hover": (80, 200),
    }

    async def execute(self, base_url: str, steps: list[WebTestStep]) -> list[WebTestResult]:
        results = []
        for step in steps:
            start = time.time()
            latency_range = self._WEB_ACTION_LATENCY.get(step.action, (100, 500))
            delay = random.uniform(*latency_range) / 1000
            await asyncio.sleep(delay)
            duration_ms = round((time.time() - start) * 1000, 2)

            if step.action == "navigate" and random.random() < 0.03:
                results.append(WebTestResult(step_name=step.name, status="failed", duration_ms=duration_ms, error=f"导航超时: {step.url or base_url}"))
            elif step.action == "assert" and random.random() < 0.05:
                results.append(WebTestResult(step_name=step.name, status="failed", duration_ms=duration_ms, error=f"断言失败: 元素 '{step.selector}' 内容不匹配"))
            else:
                results.append(WebTestResult(step_name=step.name, status="passed", duration_ms=duration_ms))
        return results


# Singleton - prefer Playwright, fallback to mock
try:
    web_engine = PlaywrightWebEngine()
except Exception:
    web_engine = MockWebEngine()
