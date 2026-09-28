"""Trusted, host-side binary-classification metrics and output validation."""

from __future__ import annotations

import math


class PredictionContractError(ValueError):
    pass


def validate_predictions(prediction: dict, expected_ids: list[str]) -> list[float]:
    """Require exact row alignment and actual class/probability contract."""
    if not isinstance(prediction, dict):
        raise PredictionContractError("Predictions must be a JSON object")
    ids = prediction.get("row_ids")
    if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
        raise PredictionContractError("row_ids must be strings")
    if len(set(ids)) != len(ids) or ids != expected_ids:
        raise PredictionContractError("Missing, duplicate, or reordered validation row IDs")
    classes = prediction.get("classes")
    if (
        not isinstance(classes, list)
        or len(classes) != 2
        or any(type(label) is not int for label in classes)
        or set(classes) != {0, 1}
    ):
        raise PredictionContractError("Classifier classes must be distinct integer labels 0 and 1")
    values = prediction.get("probabilities")
    if not isinstance(values, list) or len(values) != len(expected_ids):
        raise PredictionContractError("Probability row count does not match validation IDs")
    positive_column = classes.index(1)
    scores = []
    for row in values:
        if not isinstance(row, list) or len(row) != 2:
            raise PredictionContractError("Probabilities must have shape [N, 2]")
        if any(
            type(item) not in {int, float} or not math.isfinite(item) or not 0 <= item <= 1
            for item in row
        ):
            raise PredictionContractError("Probabilities must be finite numbers in [0, 1]")
        if not math.isclose(sum(row), 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise PredictionContractError("Each probability row must sum to one")
        scores.append(float(row[positive_column]))
    return scores


def binary_metrics(labels: list[int], scores: list[float]) -> dict:
    """Evaluate fixed 0.5 threshold plus a deterministic top-10% campaign budget.

    No threshold is optimized against these validation labels. All metrics are
    validation metrics, not an estimate from the sealed final test.
    """
    from sklearn.metrics import average_precision_score, f1_score, roc_auc_score

    from capability_factory.plugins import evaluate_metrics

    if not labels or len(labels) != len(scores):
        raise PredictionContractError("Labels/scores must be non-empty and aligned")
    if any(type(label) is not int or label not in (0, 1) for label in labels):
        raise PredictionContractError("Labels must contain only integers 0 and 1")
    if set(labels) != {0, 1}:
        raise PredictionContractError("Both classes are required for AP and ROC AUC evaluation")
    if any(not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
        raise PredictionContractError("Scores must be finite probabilities")
    top_count = max(1, math.ceil(0.1 * len(labels)))
    selected = sorted(range(len(scores)), key=lambda index: (-scores[index], index))[:top_count]
    top_positives = sum(labels[index] for index in selected)
    positive_rate = sum(labels) / len(labels)
    precision = top_positives / top_count
    return {
        "average_precision": float(average_precision_score(labels, scores)),
        "roc_auc": float(roc_auc_score(labels, scores)),
        "f1_threshold_0_5": float(
            f1_score(labels, [int(score >= 0.5) for score in scores], zero_division=0)
        ),
        "precision_at_10pct": precision,
        "recall_at_10pct": top_positives / sum(labels),
        "lift_at_10pct": precision / positive_rate,
        "validation_positive_rate": positive_rate,
        "top_10pct_count": top_count,
        "validation_rows": len(labels),
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": False,
        "ranking_tie_break": "original_validation_row_order",
        **evaluate_metrics(labels, scores),
    }
