from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field


@dataclass
class AIEvalResult:
    model_version: str
    dataset_name: str
    accuracy: float
    recall: float
    f1_score: float
    avg_latency_ms: float
    total_samples: int
    failed_samples: int
    failed_cases: list[dict] = field(default_factory=list)


# 模拟不同模型版本的基准性能
_MODEL_PROFILES = {
    "v1.0": {"accuracy": 0.89, "recall": 0.85, "f1": 0.87, "latency": 45.0},
    "v1.1": {"accuracy": 0.92, "recall": 0.88, "f1": 0.90, "latency": 42.0},
    "v2.0": {"accuracy": 0.95, "recall": 0.93, "f1": 0.94, "latency": 38.0},
    "v2.1": {"accuracy": 0.96, "recall": 0.94, "f1": 0.95, "latency": 35.0},
    "v3.0": {"accuracy": 0.97, "recall": 0.96, "f1": 0.96, "latency": 28.0},
}

# 模拟常见 SKU 类别
_SKU_CLASSES = [
    "可口可乐330ml", "百事可乐330ml", "农夫山泉550ml", "康师傅冰红茶500ml",
    "红牛250ml", "元气森林480ml", "伊利纯牛奶250ml", "蒙牛酸奶200g",
    "乐事薯片75g", "奥利奥饼干97g", "德芙巧克力43g", "统一方便面108g",
]


class AIVerifyEngine:
    """AI 识别验证引擎 - 模拟 SKU 识别模型评测"""

    async def evaluate_model(
        self,
        model_path: str,
        dataset_path: str,
        model_version: str,
    ) -> AIEvalResult:
        """执行模型评测 - 模拟推理过程"""
        profile = _MODEL_PROFILES.get(model_version, _MODEL_PROFILES["v2.0"])

        # 模拟不同数据集规模
        dataset_sizes = {"small": 100, "medium": 500, "large": 2000}
        total_samples = dataset_sizes.get(dataset_path, 500)

        # 模拟逐样本推理
        base_accuracy = profile["accuracy"]
        base_recall = profile["recall"]
        base_latency = profile["latency"]

        failed_cases = []
        failed_count = 0

        for i in range(total_samples):
            # 模拟推理延迟
            latency = base_latency + random.gauss(0, 5)
            latency = max(10.0, latency)

            # 按概率模拟识别失败
            if random.random() > base_accuracy:
                failed_count += 1
                if len(failed_cases) < 20:  # 只记录前 20 个失败用例
                    true_sku = random.choice(_SKU_CLASSES)
                    pred_sku = random.choice([s for s in _SKU_CLASSES if s != true_sku])
                    failed_cases.append({
                        "sample_id": i,
                        "true_label": true_sku,
                        "predicted_label": pred_sku,
                        "confidence": round(random.uniform(0.3, 0.7), 3),
                        "image_path": f"datasets/{dataset_path}/img_{i:05d}.jpg",
                    })

            # 每 100 个样本让出控制权
            if i % 100 == 0:
                await asyncio.sleep(0.01)

        actual_accuracy = round(1 - failed_count / total_samples, 4)
        # recall 和 f1 基于 accuracy 加噪声
        actual_recall = round(min(1.0, actual_accuracy + random.gauss(0, 0.02)), 4)
        actual_f1 = round(2 * actual_accuracy * actual_recall / (actual_accuracy + actual_recall + 1e-8), 4)
        avg_latency = round(base_latency + random.gauss(0, 3), 2)

        return AIEvalResult(
            model_version=model_version,
            dataset_name=dataset_path,
            accuracy=actual_accuracy,
            recall=actual_recall,
            f1_score=actual_f1,
            avg_latency_ms=avg_latency,
            total_samples=total_samples,
            failed_samples=failed_count,
            failed_cases=failed_cases,
        )

    async def compare_models(
        self,
        model_a_version: str,
        model_b_version: str,
        dataset_path: str,
    ) -> dict:
        """对比两个模型版本"""
        profile_a = _MODEL_PROFILES.get(model_a_version, _MODEL_PROFILES["v2.0"])
        profile_b = _MODEL_PROFILES.get(model_b_version, _MODEL_PROFILES["v2.0"])

        # 添加随机波动
        acc_a = round(profile_a["accuracy"] + random.gauss(0, 0.01), 4)
        acc_b = round(profile_b["accuracy"] + random.gauss(0, 0.01), 4)
        recall_a = round(profile_a["recall"] + random.gauss(0, 0.01), 4)
        recall_b = round(profile_b["recall"] + random.gauss(0, 0.01), 4)
        latency_a = round(profile_a["latency"] + random.gauss(0, 2), 2)
        latency_b = round(profile_b["latency"] + random.gauss(0, 2), 2)

        delta_acc = round(acc_b - acc_a, 4)
        regression = delta_acc < -0.02  # 准确率下降超过 2% 视为回归

        return {
            "model_a": {
                "version": model_a_version,
                "accuracy": acc_a,
                "recall": recall_a,
                "avg_latency_ms": latency_a,
            },
            "model_b": {
                "version": model_b_version,
                "accuracy": acc_b,
                "recall": recall_b,
                "avg_latency_ms": latency_b,
            },
            "delta": {
                "accuracy": delta_acc,
                "recall": round(recall_b - recall_a, 4),
                "avg_latency_ms": round(latency_b - latency_a, 2),
            },
            "regression_detected": regression,
            "recommendation": "建议上线" if not regression else "存在回归，不建议上线",
        }


ai_engine = AIVerifyEngine()
