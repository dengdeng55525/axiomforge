"""Variant names are checked against actual constructor parameters and parents."""

import pytest

from capability_factory.contracts import CandidatePlan
from capability_factory.execution import analyze_code, reference_code
from capability_factory.search import check_variant


def metadata(algorithm, **parameters):
    return {"actual_algorithm": algorithm, "classifier_parameters": parameters}


def plan(algorithm, variant):
    return {"algorithm": algorithm, "variant": variant}


@pytest.mark.parametrize(
    "algorithm,variant,parameters",
    [
        ("logistic", "balanced", {"class_weight": "balanced"}),
        ("forest", "balanced", {"class_weight": "balanced_subsample"}),
        ("extra_trees", "balanced", {"class_weight": "balanced"}),
        ("logistic", "regularized", {"C": 0.25}),
        ("nb", "regularized", {"alpha": 2}),
        ("forest", "regularized", {"min_samples_leaf": 2}),
        ("extra_trees", "regularized", {"min_samples_leaf": 5}),
        ("forest", "shallower", {"max_depth": 12}),
        ("extra_trees", "shallower", {"max_depth": 6}),
    ],
)
def test_initial_variants_require_real_parameter_effects(algorithm, variant, parameters):
    assert check_variant(plan(algorithm, variant), metadata(algorithm, **parameters)) is None


@pytest.mark.parametrize(
    "algorithm,variant,parameters",
    [
        ("logistic", "balanced", {}),
        ("logistic", "balanced", {"class_weight": "balanced_subsample"}),
        ("forest", "balanced", {"class_weight": None}),
        ("extra_trees", "balanced", {"class_weight": {0: 1, 1: 1}}),
        ("logistic", "regularized", {}),
        ("logistic", "regularized", {"C": 2}),
        ("logistic", "regularized", {"C": 0.25, "penalty": None}),
        ("nb", "regularized", {"alpha": 0.5}),
        ("forest", "regularized", {}),
        ("extra_trees", "regularized", {"min_samples_leaf": 1}),
        ("forest", "shallower", {"max_depth": 13}),
        ("extra_trees", "shallower", {"max_depth": None}),
    ],
)
def test_label_only_or_wrong_direction_variants_fail(algorithm, variant, parameters):
    assert check_variant(plan(algorithm, variant), metadata(algorithm, **parameters))


@pytest.mark.parametrize(
    "algorithm,parameter,variant,baseline,good,bad",
    [
        ("logistic", "C", "regularized", 0.1, 0.05, 0.25),
        ("nb", "alpha", "regularized", 3.0, 4.0, 2.0),
        ("forest", "min_samples_leaf", "regularized", 10, 12, 5),
        ("extra_trees", "min_samples_leaf", "regularized", 0.02, 0.05, 0.01),
        ("forest", "max_depth", "shallower", 6, 4, 8),
    ],
)
def test_children_compare_actual_parent_values_not_initial_defaults(
    algorithm, parameter, variant, baseline, good, bad
):
    parent = metadata(algorithm, **{parameter: baseline, "class_weight": "balanced"})
    assert (
        check_variant(plan(algorithm, variant), metadata(algorithm, **{parameter: good}), parent)
        is None
    )
    assert check_variant(plan(algorithm, variant), metadata(algorithm, **{parameter: bad}), parent)
    assert check_variant(
        plan(algorithm, variant), metadata(algorithm, **{parameter: baseline}), parent
    )


@pytest.mark.parametrize("value", [True, False, "0.25", None, float("inf"), float("nan"), -1, 0])
def test_logistic_numeric_contract_rejects_invalid_types_and_values(value):
    assert check_variant(plan("logistic", "regularized"), metadata("logistic", C=value))


@pytest.mark.parametrize(
    "algorithm,parameter,variant",
    [
        ("nb", "alpha", "regularized"),
        ("forest", "min_samples_leaf", "regularized"),
        ("forest", "max_depth", "shallower"),
    ],
)
def test_booleans_cannot_masquerade_as_numeric_parameters(algorithm, parameter, variant):
    assert check_variant(plan(algorithm, variant), metadata(algorithm, **{parameter: True}))


def test_nb_default_and_clipped_smoothing_are_handled_as_actual_values():
    p = plan("nb", "regularized")
    assert check_variant(p, metadata("nb", alpha=0.5), metadata("nb", alpha=0)) is None
    assert check_variant(p, metadata("nb", alpha=0.75), metadata("nb"))
    assert check_variant(p, metadata("nb", alpha=2), metadata("nb")) is None
    assert check_variant(
        p,
        metadata("nb", alpha=1e-11, force_alpha=False),
        metadata("nb", alpha=1e-12, force_alpha=False),
    )
    assert (
        check_variant(
            p,
            metadata("nb", alpha=1e-8, force_alpha=False),
            metadata("nb", alpha=1e-12, force_alpha=False),
        )
        is None
    )


def test_fractional_leaf_values_cannot_be_compared_to_counts_without_row_count():
    p = plan("forest", "regularized")
    assert "same unit" in check_variant(
        p, metadata("forest", min_samples_leaf=0.1), metadata("forest", min_samples_leaf=5)
    )
    assert (
        check_variant(
            p, metadata("forest", min_samples_leaf=0.2), metadata("forest", min_samples_leaf=0.1)
        )
        is None
    )


def test_shallower_from_unbounded_parent_and_default_unconstrained():
    assert (
        check_variant(
            plan("forest", "shallower"),
            metadata("forest", max_depth=20),
            metadata("forest", max_depth=None),
        )
        is None
    )
    assert check_variant(plan("forest", "default"), metadata("forest", max_depth=None)) is None


def test_incompatible_variants_and_parent_algorithm_are_rejected():
    assert check_variant(plan("dummy", "balanced"), metadata("dummy"))
    assert check_variant(plan("logistic", "balanced"), metadata("forest", class_weight="balanced"))
    assert check_variant(
        plan("logistic", "regularized"), metadata("logistic", C=0.1), metadata("nb", alpha=1)
    )


@pytest.mark.parametrize(
    "algorithm,variant",
    [
        ("logistic", "balanced"),
        ("logistic", "regularized"),
        ("forest", "balanced"),
        ("forest", "regularized"),
        ("forest", "shallower"),
        ("extra_trees", "regularized"),
        ("nb", "regularized"),
    ],
)
def test_real_reference_constructor_metadata_passes_variant_contract(algorithm, variant):
    task = "text_binary_classification" if algorithm == "nb" else "tabular_binary_classification"
    spec = {
        "task_type": task,
        "seed": 42,
        "numeric_features": ["age"],
        "categorical_features": ["job"],
        "feature_names": ["age", "job"],
    }
    actual = analyze_code(reference_code(task, algorithm, variant), spec)
    parent = analyze_code(reference_code(task, algorithm, "default"), spec)
    proposed = CandidatePlan(
        candidate_id="child",
        algorithm=algorithm,
        variant=variant,
        rationale="test actual metadata",
        parent_id="parent",
    )
    assert check_variant(proposed, actual, parent) is None
