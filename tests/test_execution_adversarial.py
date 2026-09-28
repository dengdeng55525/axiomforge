"""Offline adversarial constructor/evidence checks; attack strings are never executed."""

import copy
import json

import pytest

from capability_factory.execution import analyze_code, reference_code
from capability_factory.execution.compiler import CodePolicyError, compile_constructors
from capability_factory.execution.runner import _validate_worker_evidence
from capability_factory.execution.worker import check_prediction_stability

SPEC = {
    "task_type": "tabular_binary_classification",
    "numeric_features": ["age"],
    "categorical_features": ["job"],
    "feature_names": ["age", "job"],
    "positive_label": "yes",
    "seed": 42,
}


def test_prediction_stability_allows_only_float_summation_noise():
    result = check_prediction_stability([[0.7, 0.3]], [[0.7 + 1e-16, 0.3 - 1e-16]])
    assert 0 < result["max_abs_delta"] < 1e-14
    assert result["rtol"] == 1e-12
    with pytest.raises(ValueError, match="drift exceeds"):
        check_prediction_stability([[0.7, 0.3]], [[0.700001, 0.299999]])
    with pytest.raises(ValueError, match="non-finite"):
        check_prediction_stability([[0.7, 0.3]], [[float("nan"), 0.3]])


@pytest.mark.parametrize(
    "module,name,expression",
    [
        ("sklearn.feature_extraction.text", "TfidfVectorizer", "TfidfVectorizer(input='file')"),
        ("sklearn.feature_extraction.text", "TfidfVectorizer", "TfidfVectorizer(input='filename')"),
        ("sklearn.feature_extraction.text", "CountVectorizer", "CountVectorizer(input='filename')"),
        ("sklearn.feature_extraction.text", "CountVectorizer", "CountVectorizer('filename')"),
        (
            "sklearn.feature_extraction.text",
            "TfidfVectorizer",
            "TfidfVectorizer(tokenizer='callback')",
        ),
        (
            "sklearn.feature_extraction.text",
            "TfidfVectorizer",
            "TfidfVectorizer(preprocessor='callback')",
        ),
        (
            "sklearn.feature_extraction.text",
            "TfidfVectorizer",
            "TfidfVectorizer(analyzer='callback')",
        ),
        ("sklearn.preprocessing", "FunctionTransformer", "FunctionTransformer()"),
        (
            "sklearn.preprocessing",
            "OneHotEncoder",
            "OneHotEncoder(feature_name_combiner=lambda x,y: x)",
        ),
        ("sklearn.pipeline", "Pipeline", "Pipeline([], '/tmp/cache')"),
        ("sklearn.pipeline", "Pipeline", "Pipeline([], memory='/tmp/cache')"),
        (
            "sklearn.ensemble",
            "RandomForestClassifier",
            "RandomForestClassifier(n_jobs=-1,random_state=42)",
        ),
        (
            "sklearn.ensemble",
            "RandomForestClassifier",
            "RandomForestClassifier(n_jobs=3,random_state=42)",
        ),
        ("sklearn.compose", "ColumnTransformer", "ColumnTransformer([],n_jobs=-1)"),
        (
            "sklearn.ensemble",
            "RandomForestClassifier",
            "RandomForestClassifier(n_estimators=1001,random_state=42)",
        ),
        (
            "sklearn.ensemble",
            "RandomForestClassifier",
            "RandomForestClassifier(max_depth=65,random_state=42)",
        ),
        ("sklearn.linear_model", "LogisticRegression", "LogisticRegression(max_iter=10001)"),
        (
            "sklearn.feature_extraction.text",
            "CountVectorizer",
            "CountVectorizer(max_features=100001)",
        ),
        ("sklearn.linear_model", "LogisticRegression", "LogisticRegression(C=1e309)"),
        ("sklearn.linear_model", "LogisticRegression", "LogisticRegression(C=" + "9" * 400 + ")"),
        ("sklearn.tree", "DecisionTreeClassifier", "DecisionTreeClassifier()"),
        ("sklearn.ensemble", "ExtraTreesClassifier", "ExtraTreesClassifier(random_state=None)"),
    ],
)
def test_callbacks_paths_oversubscription_and_numeric_bombs_are_rejected(module, name, expression):
    source = (
        f"from sklearn.pipeline import Pipeline\nfrom {module} import {name}\n"
        f"def build_pipeline(task_spec):\n    return Pipeline([('model', {expression})])\n"
    )
    with pytest.raises(CodePolicyError):
        compile_constructors(source, SPEC)


def test_oversubscription_bound_respects_requested_single_cpu():
    source = reference_code(SPEC["task_type"], "forest")
    with pytest.raises(CodePolicyError, match="between 1 and 1"):
        compile_constructors(source, SPEC, cpu_limit=1)


@pytest.mark.parametrize(
    "algorithm,class_name",
    [
        ("logistic", "LogisticRegression"),
        ("forest", "RandomForestClassifier"),
        ("extra_trees", "ExtraTreesClassifier"),
        ("dummy", "DummyClassifier"),
    ],
)
def test_actual_algorithm_metadata_is_deterministic(algorithm, class_name):
    source = reference_code(SPEC["task_type"], algorithm)
    actual = analyze_code(source, SPEC)
    assert actual == analyze_code(source, SPEC)
    assert actual["actual_algorithm"] == algorithm
    assert actual["classifier_class"] == class_name
    assert actual["classifier_path"] == ["model"]
    assert json.loads(json.dumps(actual)) == actual


def test_actual_algorithm_tracks_nested_final_pipeline_not_other_constructors():
    source = """from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def build_pipeline(task_spec):
    unused = RandomForestClassifier(random_state=42)
    final = Pipeline(steps=[('actual', LogisticRegression(max_iter=200, C=0.25))])
    return Pipeline([('nested', final)])
"""
    actual = analyze_code(source, SPEC)
    assert actual["actual_algorithm"] == "logistic"
    assert actual["classifier_path"] == ["nested", "actual"]
    assert actual["classifier_parameters"]["C"] == 0.25
    assert "RandomForestClassifier" not in actual["constructor_classes"]


def _good_evidence():
    return {
        "robustness_checks": [
            {"name": name, "passed": True}
            for name in (
                "single_row",
                "repeat_prediction",
                "empty_batch_wrapper",
                "unknown_category",
                "missing_numeric",
            )
        ],
        "environment_contract": {
            "api_key_environment_present": False,
            "validation_labels_received": False,
            "test_received": False,
        },
    }


@pytest.mark.parametrize("value", [False, 0, 1, "true", None])
def test_robustness_check_must_be_explicit_true(value):
    evidence = _good_evidence()
    evidence["robustness_checks"][0]["passed"] = value
    with pytest.raises(ValueError, match="did not pass"):
        _validate_worker_evidence(evidence, SPEC["task_type"])


def test_missing_duplicate_or_malformed_robustness_check_fails_closed():
    valid = _good_evidence()
    assert len(_validate_worker_evidence(valid, SPEC["task_type"])) == 5
    for corrupt in (
        [],
        valid["robustness_checks"][:-1],
        [None],
        valid["robustness_checks"] + [valid["robustness_checks"][0]],
    ):
        evidence = copy.deepcopy(valid)
        evidence["robustness_checks"] = corrupt
        with pytest.raises(ValueError):
            _validate_worker_evidence(evidence, SPEC["task_type"])


@pytest.mark.parametrize(
    "key", ["api_key_environment_present", "validation_labels_received", "test_received"]
)
@pytest.mark.parametrize("value", [True, None, 0, "false"])
def test_clean_environment_requires_explicit_negative_evidence(key, value):
    evidence = _good_evidence()
    evidence["environment_contract"][key] = value
    with pytest.raises(ValueError, match="evidence is missing or failed"):
        _validate_worker_evidence(evidence, SPEC["task_type"])
