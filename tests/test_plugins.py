"""Trusted registry extension must preserve metric and independent-code-validation boundaries."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from capability_factory import plugins
from capability_factory.execution.reference import reference_code

TABULAR = "tabular_binary_classification"
TEXT = "text_binary_classification"


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    monkeypatch.setattr(plugins, "_METRICS", {})
    monkeypatch.setattr(plugins, "_TEMPLATES", {})


def test_registry_starts_empty_and_brier_example_is_explicit():
    assert plugins.evaluate_metrics([0, 1], [0.1, 0.8]) == {}
    plugins.register_builtin_examples()
    assert plugins.evaluate_metrics([0, 1], [0.1, 0.8]) == pytest.approx({"plugin_brier_loss": 0.025})
    assert plugins.brier_loss([0, 1], [0.0, 1.0]) == 0
    assert plugins.brier_loss([0, 1], [1.0, 0.0]) == 1


def test_metric_namespace_cannot_replace_a_core_metric():
    plugins.register_metric("average_precision", lambda labels, scores: 0.25)
    assert plugins.evaluate_metrics([0, 1], [0.1, 0.9]) == {"plugin_average_precision": 0.25}


def test_metric_and_template_collisions_are_rejected():
    metric = lambda labels, scores: 0.0  # noqa: E731
    plugins.register_metric("example", metric)
    with pytest.raises(plugins.PluginError, match="already registered"):
        plugins.register_metric("example", metric)
    plugins.register_template(TABULAR, "logistic", reference_code)
    with pytest.raises(plugins.PluginError, match="already registered"):
        plugins.register_template(TABULAR, "logistic", reference_code)


@pytest.mark.parametrize("result", [float("nan"), float("inf"), -float("inf"), "0.5", None, True, [0.5], 1j])
def test_malicious_or_invalid_metric_results_fail_closed(result):
    plugins.register_metric("invalid", lambda labels, scores: result)
    with pytest.raises(plugins.PluginError):
        plugins.evaluate_metrics([0, 1], [0.2, 0.8])


def test_metric_exception_is_reported_instead_of_zero():
    def broken(labels, scores):
        raise RuntimeError("example failure")
    plugins.register_metric("broken", broken)
    with pytest.raises(plugins.PluginError, match="broken.*RuntimeError"):
        plugins.evaluate_metrics([0, 1], [0.1, 0.8])


def test_snapshot_is_stable_when_plugin_registers_another_metric():
    registered = []

    def first(labels, scores):
        if not registered:
            plugins.register_metric("second", lambda labels, scores: 2)
            registered.append(True)
        return 1

    plugins.register_metric("first", first)
    assert plugins.evaluate_metrics([0, 1], [0.1, 0.9]) == {"plugin_first": 1.0}
    assert plugins.evaluate_metrics([0, 1], [0.1, 0.9]) == {"plugin_first": 1.0, "plugin_second": 2.0}


def test_plugins_cannot_mutate_evaluator_input_sequences():
    labels, scores = [0, 1], [0.1, 0.9]

    def mutating(received_labels, received_scores):
        received_labels[0] = 1
        return 0.0

    plugins.register_metric("mutating", mutating)
    with pytest.raises(plugins.PluginError, match="TypeError"):
        plugins.evaluate_metrics(labels, scores)
    assert labels == [0, 1]
    assert scores == [0.1, 0.9]


def test_concurrent_duplicate_registration_has_exactly_one_winner():
    def register(_):
        try:
            plugins.register_metric("same", lambda labels, scores: 1.0)
            return True
        except plugins.PluginError:
            return False
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(register, range(20)))
    assert sum(results) == 1
    assert plugins.evaluate_metrics([0, 1], [0.1, 0.9]) == {"plugin_same": 1.0}


def test_fallback_preserves_existing_reference_and_variant():
    assert plugins.get_reference_code(TABULAR, "logistic", "balanced") == reference_code(TABULAR, "logistic", "balanced")
    assert plugins.get_reference_code(TEXT, "nb") == reference_code(TEXT, "nb")


def test_modified_valid_template_reaches_registry_and_stays_ast_valid():
    from capability_factory.execution.compiler import analyze_code

    observed = []

    def modified(task_type, algorithm, variant):
        observed.append((task_type, algorithm, variant))
        return reference_code(task_type, algorithm, variant).replace("max_iter=1000", "max_iter=500")

    plugins.register_template(TABULAR, "logistic", modified)
    code = plugins.get_reference_code(TABULAR, "logistic", "regularized")
    assert "max_iter=500" in code
    assert observed == [(TABULAR, "logistic", "regularized")]
    # Compiler construction still runs independently; registration never approves code.
    task_spec = {"seed": 42, "numeric_features": ["age"], "categorical_features": ["job"]}
    compiled = analyze_code(code, task_spec)
    assert compiled["classifier_parameters"]["max_iter"] == 500
    assert compiled["classifier_parameters"]["C"] == 0.25


def test_registry_does_not_bypass_independent_ast_rejection():
    from capability_factory.execution.compiler import CodePolicyError, compile_constructors

    plugins.register_template(TABULAR, "logistic", lambda task, algorithm, variant: "import os\ndef build_pipeline(task_spec):\n    return os.system('echo bad')\n")
    code = plugins.get_reference_code(TABULAR, "logistic")
    with pytest.raises(CodePolicyError):
        compile_constructors(code, {"seed": 42})


@pytest.mark.parametrize("task,algorithm", [("new_task", "logistic"), (TABULAR, "xgboost"), (TABULAR, "nb")])
def test_registration_does_not_add_tasks_or_algorithms(task, algorithm):
    with pytest.raises(plugins.PluginError):
        plugins.register_template(task, algorithm, reference_code)


@pytest.mark.parametrize("value", [None, "", "   ", 123])
def test_invalid_template_output_is_rejected(value):
    plugins.register_template(TEXT, "logistic", lambda task, algorithm, variant: value)
    with pytest.raises(plugins.PluginError, match="nonempty Python"):
        plugins.get_reference_code(TEXT, "logistic")


def test_invalid_registration_names_and_noncallables():
    for name in ("../../bad", "Plugin Name", "UPPER", "", 1):
        with pytest.raises(plugins.PluginError):
            plugins.register_metric(name, lambda labels, scores: 0)
    with pytest.raises(plugins.PluginError, match="callable"):
        plugins.register_metric("example", None)
    with pytest.raises(plugins.PluginError, match="callable"):
        plugins.register_template(TEXT, "logistic", None)


def test_brier_input_contract_is_explicit():
    for labels, scores in (([], []), ([0], [0.1, 0.2]), ([2], [0.1]), ([0], [float("nan")]), ([0], [1.1])):
        with pytest.raises(plugins.PluginError):
            plugins.brier_loss(labels, scores)
