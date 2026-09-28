"""Independently validate generated constructor code and score its predictions."""

from __future__ import annotations

import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

from capability_factory.datasets import public_task_spec
from capability_factory.metrics import binary_metrics, validate_predictions

from .compiler import CodePolicyError, compile_constructors, inspect_constructor_plan

BACKEND = "constrained_ast_subprocess"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def _limits(raw: dict) -> dict:
    result = {
        "timeout_s": float(raw.get("timeout_s", raw.get("candidate_timeout_s", 120))),
        "memory_mib": int(raw.get("memory_mib", raw.get("candidate_memory_mib", 2048))),
        "cpu_cores": int(raw.get("cpu_cores", raw.get("candidate_cpu_cores", raw.get("cpu", 2)))),
    }
    if not math.isfinite(result["timeout_s"]) or not 0 < result["timeout_s"] <= 1800:
        raise ValueError("Candidate wall-time limit must be between 0 and 1800 seconds")
    if not 256 <= result["memory_mib"] <= 16384:
        raise ValueError("Candidate address-space limit must be 256..16384 MiB")
    if not 1 <= result["cpu_cores"] <= 8:
        raise ValueError("Candidate CPU limit must be 1..8 cores")
    return result


def validate_candidate(
    code: str,
    task_spec: dict,
    dataset: dict,
    workdir: Path,
    limits: dict,
    cancel_check: Callable[[], bool] | None = None,
    expected_algorithm: str | None = None,
) -> dict:
    """Validate AST, run bounded trusted worker, and evaluate labels on host.

    This is a constrained construction language, not arbitrary-Python execution.
    Neither a container nor a network/filesystem namespace boundary is claimed.
    All sklearn fitting and preprocessing use training data only.
    """
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    paths = {
        "source": workdir / "model.py",
        "constructor_plan": workdir / "constructor_plan.json",
        "model_metadata": workdir / "model_metadata.json",
        "predictions": workdir / "predictions.json",
        "request": workdir / "worker_request.json",
        "stdout": workdir / "worker.stdout.log",
        "stderr": workdir / "worker.stderr.log",
        "result": workdir / "validation_result.json",
    }
    result = {
        "status": "failed",
        "checks": [],
        "metrics": {},
        "resources": {},
        "error": None,
        "artifact_paths": {},
        "containment": {
            "backend": BACKEND,
            "arbitrary_python_execution": False,
            "os_sandbox": False,
            "network_namespace": False,
            "filesystem_namespace": False,
            "source_evaluated_with_exec_or_eval": False,
            "constructors_allowlisted": True,
            "resource_limited_fresh_process": True,
            "security_scope": (
                "Restricted sklearn constructor grammar; no generated methods, "
                "callbacks, file access, network calls, loops, or dynamic imports. "
                "Trusted sklearn/native dependencies remain in the trust boundary."
            ),
        },
        "quality_status": "not_evaluated",
    }
    process = None
    stage = "input_validation"

    def check(name: str, passed: bool, detail: str = "", mandatory: bool = True):
        result["checks"].append(
            {"name": name, "passed": bool(passed), "mandatory": mandatory, "detail": detail}
        )

    def fail(error_type: str, message: str, repairable: bool):
        result["error"] = {
            "type": error_type,
            "message": message[:4000],
            "repairable": repairable,
            "stage": stage,
        }
        check(stage, False, message[:1000])

    try:
        normalized_limits = _limits(limits)
        result["resources"]["limits"] = normalized_limits
        if cancel_check is not None and cancel_check():
            fail("Cancelled", "Run cancelled before candidate execution", False)
            return _finish(result, paths, started)
        if not isinstance(code, str) or len(code.encode()) > 60000:
            raise CodePolicyError("Generated code must be a string of at most 60,000 bytes")
        paths["source"].write_text(code, encoding="utf-8")
        result["source_sha256"] = hashlib.sha256(code.encode()).hexdigest()
        for old_artifact in ("predictions", "constructor_plan", "model_metadata", "request"):
            paths[old_artifact].unlink(missing_ok=True)
        safe_spec = public_task_spec(dataset, task_spec)
        stage = "source_policy"
        plan = compile_constructors(code, safe_spec, normalized_limits["cpu_cores"])
        _write_json(paths["constructor_plan"], plan)
        result["model_metadata"] = inspect_constructor_plan(plan)
        _write_json(paths["model_metadata"], result["model_metadata"])
        check("source_policy", True, "AST parsed as approved constructors without exec/eval")
        if expected_algorithm is not None:
            stage = "plan_consistency"
            actual_algorithm = result["model_metadata"]["actual_algorithm"]
            if actual_algorithm != expected_algorithm:
                raise CodePolicyError(
                    f"Final classifier algorithm {actual_algorithm} does not match planned {expected_algorithm}"
                )
            check(
                "plan_consistency", True, f"Final classifier matches planned {expected_algorithm}"
            )

        stage = "dataset_integrity"
        train_path = Path(dataset["train_path"]).resolve()
        features_path = Path(dataset["validation_features_path"]).resolve()
        labels_path = Path(dataset["validation_labels_path"]).resolve()
        if len({train_path, features_path, labels_path}) != 3:
            raise ValueError("Training, validation features, and evaluator labels must be separate")
        file_hashes = dataset["manifest"]["file_sha256"]
        for name, path in (
            ("train", train_path),
            ("validation_features", features_path),
            ("validation_labels", labels_path),
        ):
            if _hash(path) != file_hashes[name]:
                raise ValueError(f"Prepared dataset checksum mismatch: {name}")
        expected = json.loads(labels_path.read_text())
        validation_features = json.loads(features_path.read_text())
        train = json.loads(train_path.read_text())
        if "y" in validation_features:
            raise ValueError("Validation labels must not appear in worker feature input")
        if validation_features["row_ids"] != expected["row_ids"]:
            raise ValueError("Validation feature/label row IDs are not aligned")
        if len(set(train["row_ids"])) != len(train["row_ids"]):
            raise ValueError("Training row IDs contain duplicates")
        if set(train["row_ids"]) & set(expected["row_ids"]):
            raise ValueError("Train/validation row IDs overlap")
        if len(train["row_ids"]) != len(train["X"]) or len(train["X"]) != len(train["y"]):
            raise ValueError("Training rows/features/labels are not aligned")
        if len(expected["row_ids"]) != dataset["validation_rows"]:
            raise ValueError("Validation row count disagrees with dataset contract")
        if dataset["task_type"] == "tabular_binary_classification":
            allowed = set(dataset["feature_names"])
            if any(set(row) != allowed for row in train["X"] + validation_features["X"]):
                raise ValueError("Tabular feature names violate the pre-contact feature policy")
        check(
            "dataset_integrity", True, "SHA256, split disjointness, row alignment, feature policy"
        )
        check("labels_withheld", True, "Worker receives no validation labels or final test")
        del train, validation_features

        request = {
            "code_path": str(paths["source"]),
            "train_path": str(train_path),
            "validation_features_path": str(features_path),
            "output_path": str(paths["predictions"]),
            "task_spec": safe_spec,
            "limits": normalized_limits,
        }
        _write_json(paths["request"], request)
        environment = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(workdir),
            "TMPDIR": str(workdir),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONHASHSEED": str(safe_spec["seed"]),
        }
        for variable in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        ):
            environment[variable] = str(normalized_limits["cpu_cores"])
        stage = "worker_execution"
        execution_started = time.perf_counter()
        with paths["stdout"].open("wb") as stdout, paths["stderr"].open("wb") as stderr:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-I",
                    str(Path(__file__).with_name("worker.py")),
                    str(paths["request"]),
                ],
                cwd=workdir,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            result["resources"]["worker_pid"] = process.pid
            interrupted = None
            while process.poll() is None:
                if cancel_check is not None and cancel_check():
                    interrupted = "Cancelled"
                    break
                if time.perf_counter() - execution_started >= normalized_limits["timeout_s"]:
                    interrupted = "TimeoutExceeded"
                    break
                time.sleep(min(0.05, normalized_limits["timeout_s"]))
            if interrupted:
                _terminate_process_group(process)
                result["resources"]["wall_seconds"] = time.perf_counter() - execution_started
                fail(
                    interrupted,
                    "Candidate execution cancelled"
                    if interrupted == "Cancelled"
                    else "Candidate exceeded wall-time limit; process group terminated",
                    interrupted != "Cancelled",
                )
                return _finish(result, paths, started)
        result["resources"]["wall_seconds"] = time.perf_counter() - execution_started
        if not paths["predictions"].exists():
            error_tail = paths["stderr"].read_text(errors="replace")[-2000:]
            fail("WorkerProcessError", f"Worker exited {process.returncode}; {error_tail}", True)
            return _finish(result, paths, started)
        if paths["predictions"].stat().st_size > 32 * 1024 * 1024:
            raise ValueError("Worker output exceeded 32 MiB")
        prediction = json.loads(paths["predictions"].read_text())
        result["resources"].update(prediction.get("resources", {}))
        if process.returncode != 0 or prediction.get("error"):
            error = prediction.get(
                "error", {"type": "WorkerProcessError", "message": f"exit={process.returncode}"}
            )
            if (
                error["type"] == "MemoryError"
                or "failed to map segment" in error["message"]
                or "Unable to allocate" in error["message"]
            ):
                error = {
                    "type": "ResourceLimitExceeded",
                    "message": (
                        f"Address-space limit {normalized_limits['memory_mib']} MiB "
                        f"prevented execution: {error['message']}"
                    ),
                }
            fail(error["type"], error["message"], True)
            return _finish(result, paths, started)
        check("worker_execution", True, "Resource-limited fresh process exited successfully")

        stage = "prediction_contract"
        scores = validate_predictions(prediction, expected["row_ids"])
        check(
            "prediction_contract",
            True,
            "Exact row IDs, binary classes, finite normalized Nx2 probabilities",
        )
        stage = "robustness_contract"
        for item in _validate_worker_evidence(prediction, dataset["task_type"]):
            check(item["name"], item["passed"])
        check("clean_environment", True, "No API keys/tokens passed to worker")
        stage = "host_evaluation"
        result["metrics"] = binary_metrics(expected["y"], scores)
        baseline_ap = result["metrics"]["validation_positive_rate"]
        result["metrics"]["dummy_average_precision"] = baseline_ap
        result["metrics"]["ap_improvement_over_dummy"] = (
            result["metrics"]["average_precision"] - baseline_ap
        )
        above = result["metrics"]["average_precision"] > baseline_ap + 1e-12
        result["quality_status"] = "above_prevalence" if above else "baseline_or_worse"
        check(
            "ap_above_dummy",
            above,
            "Advisory quality gate; not a substitute for sealed-test evaluation",
            mandatory=False,
        )
        check(
            "host_evaluation", True, "Metrics computed only by trusted host using validation labels"
        )
        if any(not item["passed"] for item in result["checks"] if item["mandatory"]):
            raise ValueError("A mandatory independent verification check failed")
        result["status"] = "passed"
    except Exception as error:
        if process is not None and process.poll() is None:
            _terminate_process_group(process)
        repairable = stage not in {"dataset_integrity", "input_validation"}
        fail(type(error).__name__, str(error), repairable)
    return _finish(result, paths, started)


def _validate_worker_evidence(prediction: dict, task_type: str) -> list[dict]:
    """Fail closed when mandatory worker evidence is absent or inconsistent."""
    required = {"single_row", "repeat_prediction", "empty_batch_wrapper"}
    if task_type == "tabular_binary_classification":
        required |= {"unknown_category", "missing_numeric"}
    else:
        required |= {"empty_text"}
    checks = prediction.get("robustness_checks")
    if not isinstance(checks, list):
        raise ValueError("Worker robustness evidence is missing")
    seen = set()
    for item in checks:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("Malformed worker robustness check")
        name = item["name"]
        if name in seen:
            raise ValueError(f"Duplicate worker robustness check: {name}")
        seen.add(name)
        if item.get("passed") is not True:
            raise ValueError(f"Worker robustness check did not pass: {name}")
    if not required <= seen:
        raise ValueError(f"Missing required worker robustness checks: {sorted(required - seen)}")
    environment = prediction.get("environment_contract")
    if not isinstance(environment, dict) or any(
        environment.get(key) is not False
        for key in ("api_key_environment_present", "validation_labels_received", "test_received")
    ):
        raise ValueError(
            "Worker clean-environment and label-isolation evidence is missing or failed"
        )
    return checks


def _terminate_process_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=10)


def _finish(result: dict, paths: dict, started: float) -> dict:
    result["resources"]["total_seconds"] = time.perf_counter() - started
    result["artifact_paths"] = {
        key: str(path) for key, path in paths.items() if path.exists() or key == "result"
    }
    _write_json(paths["result"], result)
    return result
