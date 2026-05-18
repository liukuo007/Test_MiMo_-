from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvalMetrics:
    accuracy: float
    recall: float
    f1_score: float
    precision: float
    total_samples: int
    correct_samples: int
    failed_samples: int


def calculate_metrics(predictions: list[str], ground_truth: list[str]) -> EvalMetrics:
    total = len(ground_truth)
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    accuracy = correct / total if total > 0 else 0

    classes = set(ground_truth) | set(predictions)
    per_class_precision = {}
    per_class_recall = {}
    per_class_f1 = {}

    for cls in classes:
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == cls and g == cls)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p == cls and g != cls)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != cls and g == cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

        per_class_precision[cls] = prec
        per_class_recall[cls] = rec
        per_class_f1[cls] = f1

    n_classes = len(classes) if classes else 1
    macro_precision = sum(per_class_precision.values()) / n_classes
    macro_recall = sum(per_class_recall.values()) / n_classes
    macro_f1 = sum(per_class_f1.values()) / n_classes

    return EvalMetrics(
        accuracy=round(accuracy, 4),
        recall=round(macro_recall, 4),
        f1_score=round(macro_f1, 4),
        precision=round(macro_precision, 4),
        total_samples=total,
        correct_samples=correct,
        failed_samples=total - correct,
    )
