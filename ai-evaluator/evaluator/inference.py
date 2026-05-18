from __future__ import annotations

import os
import time
import random
import hashlib
from dataclasses import dataclass
from typing import Optional

import structlog

from evaluator.config import config

logger = structlog.get_logger()


@dataclass
class InferenceResult:
    sku: str
    confidence: float
    bbox: list[float]
    latency_ms: float


SKU_CATALOG = [
    "可口可乐330ml", "百事可乐330ml", "农夫山泉550ml", "康师傅冰红茶500ml",
    "红牛250ml", "元气森林480ml", "伊利纯牛奶250ml", "蒙牛酸奶200g",
    "乐事薯片75g", "奥利奥饼干97g", "德芙巧克力43g", "统一方便面108g",
]


class MockInferenceEngine:
    """Mock inference engine for when no real model is available."""

    def __init__(self, model_path: str):
        self.model_path = model_path
        logger.info("mock_engine_loaded", model_path=model_path)

    def predict(self, image_path: str) -> InferenceResult:
        start = time.time()
        h = int(hashlib.md5(image_path.encode()).hexdigest(), 16)
        sku_idx = h % len(SKU_CATALOG)
        base_confidence = 0.75 + (h % 250) / 1000.0
        confidence = min(0.99, round(base_confidence + random.gauss(0, 0.03), 3))
        confidence = max(0.1, confidence)
        x1 = random.randint(10, 200)
        y1 = random.randint(10, 200)
        w = random.randint(80, 300)
        h_box = random.randint(80, 300)
        bbox = [float(x1), float(y1), float(x1 + w), float(y1 + h_box)]
        latency_ms = round((time.time() - start) * 1000 + random.uniform(15, 50), 2)
        return InferenceResult(sku=SKU_CATALOG[sku_idx], confidence=confidence, bbox=bbox, latency_ms=latency_ms)

    def predict_batch(self, image_paths: list[str]) -> list[InferenceResult]:
        return [self.predict(p) for p in image_paths]


class ONNXInferenceEngine:
    """Real inference engine using ONNX Runtime."""

    def __init__(self, model_path: str):
        import onnxruntime as ort
        self.model_path = model_path
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        logger.info("onnx_engine_loaded", model_path=model_path, providers=self.session.get_providers())

    def predict(self, image_path: str) -> InferenceResult:
        import cv2
        import numpy as np

        start = time.time()

        img = cv2.imread(image_path)
        if img is None:
            return InferenceResult(sku="unknown", confidence=0.0, bbox=[0, 0, 0, 0], latency_ms=0)

        img_resized = cv2.resize(img, (640, 640))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        input_tensor = np.expand_dims(img_transposed, axis=0)

        outputs = self.session.run(None, {self.input_name: input_tensor})

        latency_ms = round((time.time() - start) * 1000, 2)

        # Parse outputs (assuming YOLO-like output)
        detections = outputs[0]
        if len(detections.shape) >= 2 and detections.shape[0] > 0:
            best = detections[0]
            if len(best) >= 6:
                x1, y1, x2, y2, conf, cls_id = best[:6]
                sku = SKU_CATALOG[int(cls_id) % len(SKU_CATALOG)] if conf > 0.3 else "unknown"
                return InferenceResult(
                    sku=sku,
                    confidence=float(conf),
                    bbox=[float(x1), float(y1), float(x2), float(y2)],
                    latency_ms=latency_ms,
                )

        return InferenceResult(sku="unknown", confidence=0.0, bbox=[0, 0, 0, 0], latency_ms=latency_ms)

    def predict_batch(self, image_paths: list[str]) -> list[InferenceResult]:
        return [self.predict(p) for p in image_paths]


class PyTorchInferenceEngine:
    """Real inference engine using PyTorch."""

    def __init__(self, model_path: str):
        import torch
        self.model_path = model_path
        self.device = torch.device(config.DEVICE if torch.cuda.is_available() or config.DEVICE == "cpu" else "cpu")
        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()
        logger.info("pytorch_engine_loaded", model_path=model_path, device=str(self.device))

    def predict(self, image_path: str) -> InferenceResult:
        import cv2
        import torch
        import numpy as np

        start = time.time()

        img = cv2.imread(image_path)
        if img is None:
            return InferenceResult(sku="unknown", confidence=0.0, bbox=[0, 0, 0, 0], latency_ms=0)

        img_resized = cv2.resize(img, (640, 640))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = img_rgb.astype(np.float32) / 255.0
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        input_tensor = torch.from_numpy(img_transposed).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_tensor)

        latency_ms = round((time.time() - start) * 1000, 2)

        if isinstance(outputs, (list, tuple)):
            pred = outputs[0].cpu().numpy()
        else:
            pred = outputs.cpu().numpy()

        if len(pred.shape) >= 2 and pred.shape[0] > 0:
            best = pred[0]
            if len(best) >= 6:
                x1, y1, x2, y2, conf, cls_id = best[:6]
                sku = SKU_CATALOG[int(cls_id) % len(SKU_CATALOG)] if conf > 0.3 else "unknown"
                return InferenceResult(
                    sku=sku,
                    confidence=float(conf),
                    bbox=[float(x1), float(y1), float(x2), float(y2)],
                    latency_ms=latency_ms,
                )

        return InferenceResult(sku="unknown", confidence=0.0, bbox=[0, 0, 0, 0], latency_ms=latency_ms)

    def predict_batch(self, image_paths: list[str]) -> list[InferenceResult]:
        return [self.predict(p) for p in image_paths]


def create_engine(model_path: str):
    """Factory: create the appropriate engine based on model file extension."""
    if not os.path.exists(model_path):
        logger.warning("model_not_found_using_mock", model_path=model_path)
        return MockInferenceEngine(model_path)

    ext = os.path.splitext(model_path)[1].lower()

    if ext == ".onnx":
        try:
            return ONNXInferenceEngine(model_path)
        except Exception as e:
            logger.warning("onnx_load_failed_using_mock", error=str(e))
            return MockInferenceEngine(model_path)
    elif ext in (".pt", ".pth"):
        try:
            return PyTorchInferenceEngine(model_path)
        except Exception as e:
            logger.warning("pytorch_load_failed_using_mock", error=str(e))
            return MockInferenceEngine(model_path)
    else:
        logger.info("unknown_model_format_using_mock", ext=ext)
        return MockInferenceEngine(model_path)


# Keep backward-compatible name
InferenceEngine = MockInferenceEngine
