import copy

import pytest

from capability_factory.metrics import PredictionContractError, binary_metrics, validate_predictions


def test_probability_class_order_and_rank_metrics():
    predicted = {
        "row_ids": ["a", "b", "c", "d"],
        "classes": [1, 0],
        "probabilities": [[0.9, 0.1], [0.2, 0.8], [0.8, 0.2], [0.1, 0.9]],
    }
    scores = validate_predictions(predicted, ["a", "b", "c", "d"])
    result = binary_metrics([1, 0, 1, 0], scores)
    assert result["average_precision"] == 1
    assert result["roc_auc"] == 1
    assert result["f1_threshold_0_5"] == 1
    assert result["precision_at_10pct"] == 1
    assert result["lift_at_10pct"] == 2
    assert result["sealed_test_scored"] is False


@pytest.mark.parametrize(
    "patch",
    [
        {"row_ids": ["a", "a"]},
        {"row_ids": ["b", "a"]},
        {"row_ids": [0, 1]},
        {"classes": [0, 0]},
        {"classes": [False, True]},
        {"classes": ["0", "1"]},
        {"probabilities": [[0.5, 0.5]]},
        {"probabilities": [[0.5], [0.5]]},
        {"probabilities": [[float("nan"), 0.5], [0.5, 0.5]]},
        {"probabilities": [[float("inf"), 0.5], [0.5, 0.5]]},
        {"probabilities": [[-0.1, 1.1], [0.5, 0.5]]},
        {"probabilities": [[0.7, 0.7], [0.5, 0.5]]},
        {"probabilities": [[True, False], [0.5, 0.5]]},
    ],
)
def test_probability_contract_rejects_corruption(patch):
    valid = {"row_ids": ["a", "b"], "classes": [0, 1], "probabilities": [[0.5, 0.5], [0.5, 0.5]]}
    value = copy.deepcopy(valid)
    value.update(patch)
    with pytest.raises(PredictionContractError):
        validate_predictions(value, ["a", "b"])


def test_constant_prior_average_precision_is_prevalence():
    result = binary_metrics([0, 0, 0, 1], [0.25] * 4)
    assert result["average_precision"] == 0.25
    assert result["roc_auc"] == 0.5


@pytest.mark.parametrize(
    "labels,scores",
    [([], []), ([0], [0.1]), ([True, False], [0.1, 0.2]), ([0, 1], [float("nan"), 0.2])],
)
def test_metric_inputs_must_be_valid(labels, scores):
    with pytest.raises(PredictionContractError):
        binary_metrics(labels, scores)
