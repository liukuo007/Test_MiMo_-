from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class EvalReport:
    model_version: str
    dataset_name: str
    accuracy: float
    recall: float
    f1_score: float
    total_samples: int
    failed_samples: int
    failed_cases: list[dict]
    generated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def generate_report(evaluation_id: int, metrics: dict, failed_cases: Optional[list[dict]] = None) -> EvalReport:
    return EvalReport(
        model_version=metrics.get("model_version", ""),
        dataset_name=metrics.get("dataset_name", ""),
        accuracy=metrics.get("accuracy", 0),
        recall=metrics.get("recall", 0),
        f1_score=metrics.get("f1_score", 0),
        total_samples=metrics.get("total_samples", 0),
        failed_samples=metrics.get("failed_samples", 0),
        failed_cases=failed_cases or [],
        generated_at=datetime.now().isoformat(),
    )
