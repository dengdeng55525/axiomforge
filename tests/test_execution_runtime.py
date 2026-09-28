import hashlib
import json
import os
from pathlib import Path

import pytest

from capability_factory.execution import reference_code, validate_candidate
from capability_factory.execution.failures import failure_code


@pytest.fixture
def small_dataset(tmp_path):
    train = {
        "row_ids": [f"train:{i}" for i in range(120)],
        "X": [{"age": i % 30, "job": "a" if i % 2 else "b"} for i in range(120)],
        "y": [int(i % 30 > 18) for i in range(120)],
    }
    features = {
        "row_ids": [f"val:{i}" for i in range(30)],
        "X": [{"age": i, "job": "a" if i % 2 else "b"} for i in range(30)],
    }
    labels = {"row_ids": features["row_ids"], "y": [int(i > 18) for i in range(30)]}
    hashes, paths = {}, {}
    for name, value in (
        ("train", train),
        ("validation_features", features),
        ("validation_labels", labels),
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value))
        paths[name + "_path"] = str(path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "dataset_id": "test-fixture",
        "task_type": "tabular_binary_classification",
        "train_rows": 120,
        "validation_rows": 30,
        "feature_names": ["age", "job"],
        "numeric_features": ["age"],
        "categorical_features": ["job"],
        "positive_label": "yes",
        "manifest": {"file_sha256": hashes},
        **paths,
    }


def test_complete_candidate_withheld_labels_and_clean_environment(
    small_dataset, tmp_path, monkeypatch
):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-secret-that-must-never-reach-worker")
    result = validate_candidate(
        reference_code(small_dataset["task_type"]), {}, small_dataset, tmp_path / "run", {}
    )
    assert result["status"] == "passed", result["error"]
    assert result["metrics"]["average_precision"] > 0.95
    assert result["quality_status"] == "above_prevalence"
    assert result["containment"]["os_sandbox"] is False
    assert result["resources"]["peak_rss_mib"] < 2048
    checks = {item["name"]: item["passed"] for item in result["checks"]}
    for name in (
        "single_row",
        "repeat_prediction",
        "empty_batch_wrapper",
        "unknown_category",
        "missing_numeric",
        "clean_environment",
    ):
        assert checks[name]
    request = Path(result["artifact_paths"]["request"]).read_text()
    assert "validation_labels" not in request
    assert "test-only-secret" not in request
    predictions = json.loads(Path(result["artifact_paths"]["predictions"]).read_text())
    assert predictions["environment_contract"]["api_key_environment_present"] is False


def test_baseline_is_scoreable_without_faking_quality(small_dataset, tmp_path):
    result = validate_candidate(
        reference_code(small_dataset["task_type"], "dummy"),
        {},
        small_dataset,
        tmp_path / "dummy",
        {},
    )
    assert result["status"] == "passed", result["error"]
    assert result["quality_status"] == "baseline_or_worse"
    assert result["metrics"]["ap_improvement_over_dummy"] == pytest.approx(0)


@pytest.mark.parametrize("case", ["unknown_parameter", "unknown_category", "missing_imputer"])
def test_runtime_failure_has_actionable_repair_evidence(case, small_dataset, tmp_path):
    result = validate_candidate(failure_code(case), {}, small_dataset, tmp_path / case, {})
    assert result["status"] == "failed"
    assert result["error"]["repairable"] is True
    assert result["error"]["message"]
    assert result["metrics"] == {}


def test_policy_failure_never_spawns_worker(small_dataset, tmp_path):
    result = validate_candidate(
        failure_code("policy_violation"), {}, small_dataset, tmp_path / "policy", {}
    )
    assert result["error"]["type"] == "CodePolicyError"
    assert "worker_pid" not in result["resources"]


def test_generated_classifier_must_match_plan_before_execution(small_dataset, tmp_path):
    result = validate_candidate(
        reference_code(small_dataset["task_type"], "forest"),
        {},
        small_dataset,
        tmp_path / "plan_mismatch",
        {},
        expected_algorithm="logistic",
    )
    assert result["status"] == "failed"
    assert result["error"]["stage"] == "plan_consistency"
    assert result["error"]["repairable"] is True
    assert result["model_metadata"]["actual_algorithm"] == "forest"
    assert "worker_pid" not in result["resources"]


@pytest.mark.parametrize("corruption", ["false", "missing", "bad_environment"])
def test_runner_rejects_invalid_worker_evidence(small_dataset, tmp_path, monkeypatch, corruption):
    """Inject worker JSON at the process boundary; execute no attack source."""
    from capability_factory.execution import runner

    labels = json.loads(Path(small_dataset["validation_labels_path"]).read_text())
    evidence = {
        "row_ids": labels["row_ids"],
        "classes": [0, 1],
        "probabilities": [[0.5, 0.5]] * len(labels["row_ids"]),
        "resources": {},
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
    if corruption == "false":
        evidence["robustness_checks"][0]["passed"] = False
    elif corruption == "missing":
        evidence["robustness_checks"].pop()
    else:
        evidence["environment_contract"]["test_received"] = True

    class CompletedWorker:
        pid = 999999999
        returncode = 0

        def __init__(self, *args, **kwargs):
            (Path(kwargs["cwd"]) / "predictions.json").write_text(json.dumps(evidence))

        def poll(self):
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", CompletedWorker)
    result = validate_candidate(
        reference_code(small_dataset["task_type"]),
        {},
        small_dataset,
        tmp_path / "bad_evidence",
        {},
        expected_algorithm="logistic",
    )
    assert result["status"] == "failed"
    assert result["error"]["stage"] == "robustness_contract"
    assert result["metrics"] == {}


def test_timeout_terminates_process_group(small_dataset, tmp_path):
    result = validate_candidate(
        reference_code(small_dataset["task_type"]),
        {},
        small_dataset,
        tmp_path / "timeout",
        {"timeout_s": 0.005},
    )
    assert result["error"]["type"] == "TimeoutExceeded"
    assert result["resources"]["wall_seconds"] < 1
    with pytest.raises(ProcessLookupError):
        os.kill(result["resources"]["worker_pid"], 0)


def test_cancellation_terminates_running_worker(small_dataset, tmp_path):
    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls >= 3

    result = validate_candidate(
        reference_code(small_dataset["task_type"]),
        {},
        small_dataset,
        tmp_path / "cancel",
        {},
        cancel_check=cancel,
    )
    assert result["error"]["type"] == "Cancelled"
    assert result["error"]["repairable"] is False
    with pytest.raises(ProcessLookupError):
        os.kill(result["resources"]["worker_pid"], 0)


def test_dataset_corruption_is_not_repaired_by_model(small_dataset, tmp_path):
    Path(small_dataset["validation_features_path"]).write_text("{}")
    result = validate_candidate(
        reference_code(small_dataset["task_type"]), {}, small_dataset, tmp_path / "corrupt", {}
    )
    assert result["status"] == "failed"
    assert result["error"]["stage"] == "dataset_integrity"
    assert result["error"]["repairable"] is False
    assert "worker_pid" not in result["resources"]


@pytest.mark.parametrize("algorithm", ["logistic", "forest"])
def test_same_seed_yields_identical_predictions(small_dataset, tmp_path, algorithm):
    results = [
        validate_candidate(
            reference_code(small_dataset["task_type"], algorithm),
            {"seed": 42},
            small_dataset,
            tmp_path / f"repeat{i}",
            {},
        )
        for i in range(2)
    ]
    assert all(result["status"] == "passed" for result in results)
    predictions = [
        json.loads(Path(result["artifact_paths"]["predictions"]).read_text()) for result in results
    ]
    assert predictions[0]["probabilities"] == predictions[1]["probabilities"]
    assert results[0]["metrics"] == results[1]["metrics"]


def test_low_memory_limit_is_enforced(small_dataset, tmp_path):
    result = validate_candidate(
        reference_code(small_dataset["task_type"]),
        {},
        small_dataset,
        tmp_path / "low_memory",
        {"memory_mib": 256, "timeout_s": 20},
    )
    assert result["status"] == "failed"
    assert result["error"]["type"] in {"ResourceLimitExceeded", "WorkerProcessError"}
    assert result["resources"]["wall_seconds"] < 20
