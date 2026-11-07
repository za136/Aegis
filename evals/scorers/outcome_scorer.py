"""Outcome Accuracy and Classification Metrics Scorer."""

from typing import Any, Dict, List
from pydantic import BaseModel


class ClassificationMetrics(BaseModel):
    total_cases: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float
    false_positive_rate: float


def compute_binary_metrics(
    predictions: List[bool], ground_truth: List[bool]
) -> ClassificationMetrics:
    """Compute standard binary classification metrics with focus on false negative rate."""
    if len(predictions) != len(ground_truth):
        raise ValueError("Length mismatch between predictions and ground truth.")

    tp = sum(1 for p, g in zip(predictions, ground_truth) if p and g)
    tn = sum(1 for p, g in zip(predictions, ground_truth) if not p and not g)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p and not g)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if not p and g)

    total = len(predictions)
    acc = round((tp + tn) / total, 4) if total > 0 else 0.0
    prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
    rec = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
    f1 = round(2 * (prec * rec) / (prec + rec), 4) if (prec + rec) > 0 else 0.0
    fnr = round(fn / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    fpr = round(fp / (tn + fp), 4) if (tn + fp) > 0 else 0.0

    return ClassificationMetrics(
        total_cases=total,
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1_score=f1,
        false_negative_rate=fnr,
        false_positive_rate=fpr,
    )
