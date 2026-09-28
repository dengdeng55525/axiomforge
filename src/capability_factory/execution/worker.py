"""Trusted, fresh-process worker for a constrained estimator constructor plan.

The environment is scrubbed by the parent. Resource limits are installed before
numeric libraries are imported. Source is parsed twice; it is never exec/eval'd.
This process is NOT an OS/filesystem/network security sandbox.
"""

from __future__ import annotations

import json
import math
import os
import resource
import sys
import time
from pathlib import Path


def _limit_resources(limits: dict) -> None:
    memory_bytes = int(limits["memory_mib"]) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    cpu_seconds = max(1, math.ceil(float(limits["timeout_s"]) * int(limits["cpu_cores"])))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    if hasattr(os, "sched_getaffinity"):
        available = sorted(os.sched_getaffinity(0))
        os.sched_setaffinity(0, available[: int(limits["cpu_cores"])])


def _save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False) + "\n")


def check_prediction_stability(first, second) -> dict:
    """Allow float summation noise, while rejecting material prediction drift.

    Threaded forest reductions can sum tree probabilities in a different order.
    Tight float64 tolerance is appropriate; exact byte equality is not.
    """
    import numpy as np

    first, second = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if first.shape != second.shape or not np.isfinite(first).all() or not np.isfinite(second).all():
        raise ValueError("Repeated prediction has mismatched shape or non-finite values")
    max_abs_delta = float(np.max(np.abs(first - second))) if first.size else 0.0
    rtol, atol = 1e-12, 1e-14
    if not np.allclose(first, second, rtol=rtol, atol=atol, equal_nan=False):
        raise ValueError(
            f"Repeated prediction drift exceeds float64 tolerance: max_abs_delta={max_abs_delta}"
        )
    return {"max_abs_delta": max_abs_delta, "rtol": rtol, "atol": atol}


def main(request_path: str) -> int:
    started = time.perf_counter()
    request = json.loads(Path(request_path).read_text())
    output_path = Path(request["output_path"])
    _limit_resources(request["limits"])
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        import numpy as np
        import pandas as pd
        import sklearn
        from joblib import parallel_backend
        from threadpoolctl import threadpool_limits

        from capability_factory.execution.compiler import compile_constructors, instantiate_plan

        spec = request["task_spec"]
        source = Path(request["code_path"]).read_text()
        plan = compile_constructors(source, spec, cpu_limit=request["limits"]["cpu_cores"])
        pipeline = instantiate_plan(plan)
        train = json.loads(Path(request["train_path"]).read_text())
        validation = json.loads(Path(request["validation_features_path"]).read_text())
        if "y" in validation:
            raise ValueError("Validation-label leakage: labels found in feature-only worker input")
        if spec["task_type"] == "tabular_binary_classification":
            x_train = pd.DataFrame(train["X"], columns=spec["feature_names"])
            x_val = pd.DataFrame(validation["X"], columns=spec["feature_names"])
        else:
            x_train, x_val = train["X"], validation["X"]
        y_train = np.asarray(train["y"], dtype=np.int64)
        if set(y_train.tolist()) != {0, 1}:
            raise ValueError("Training labels must contain both binary classes")
        # Force sklearn/joblib parallel work into threads so the address-space
        # limit covers every estimator and no separate loky process escapes it.
        with (
            threadpool_limits(limits=request["limits"]["cpu_cores"]),
            parallel_backend("threading", n_jobs=request["limits"]["cpu_cores"]),
        ):
            fit_started = time.perf_counter()
            pipeline.fit(x_train, y_train)
            fit_seconds = time.perf_counter() - fit_started
            classes = pipeline.classes_.tolist()
            if len(classes) != 2 or set(classes) != {0, 1}:
                raise ValueError("Fitted estimator classes must be exactly 0 and 1")

            def predict(batch):
                if len(batch) == 0:
                    return np.empty((0, 2), dtype=float)
                result = np.asarray(pipeline.predict_proba(batch), dtype=float)
                if result.shape != (len(batch), 2) or not np.isfinite(result).all():
                    raise ValueError("predict_proba must return finite Nx2 probabilities")
                if (result < 0).any() or (result > 1).any():
                    raise ValueError("Probability values outside [0,1]")
                if not np.allclose(result.sum(axis=1), 1.0, rtol=1e-6, atol=1e-6):
                    raise ValueError("Probabilities must sum to one")
                return result

            predict_started = time.perf_counter()
            probabilities = predict(x_val)
            predict_seconds = time.perf_counter() - predict_started
            single = x_val.iloc[:1] if hasattr(x_val, "iloc") else x_val[:1]
            single_probabilities = predict(single)
            if not np.allclose(single_probabilities, probabilities[:1], rtol=1e-9, atol=1e-9):
                raise ValueError("Single-row prediction is inconsistent with batch prediction")
            repeated = predict(single)
            stability = check_prediction_stability(single_probabilities, repeated)
            empty = x_val.iloc[:0] if hasattr(x_val, "iloc") else []
            if predict(empty).shape != (0, 2):
                raise ValueError("Empty batch wrapper must return zero rows")
            robustness = [
                {"name": "single_row", "passed": True},
                {"name": "repeat_prediction", "passed": True, **stability},
                {"name": "empty_batch_wrapper", "passed": True},
            ]
            if spec["task_type"] == "tabular_binary_classification":
                unseen = single.copy(deep=True)
                for column in spec["categorical_features"]:
                    unseen[column] = "__ACF_UNSEEN_CATEGORY__"
                predict(unseen)
                robustness.append({"name": "unknown_category", "passed": True})
                missing = single.copy(deep=True)
                for column in spec["numeric_features"]:
                    missing[column] = np.nan
                predict(missing)
                robustness.append({"name": "missing_numeric", "passed": True})
            else:
                predict([""])
                robustness.append({"name": "empty_text", "passed": True})
        _save_json(
            output_path,
            {
                "row_ids": validation["row_ids"],
                "classes": classes,
                "probabilities": probabilities.tolist(),
                "resources": {
                    "fit_seconds": fit_seconds,
                    "predict_seconds": predict_seconds,
                    "worker_wall_seconds": time.perf_counter() - started,
                    "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                    "cpu_seconds": (
                        resource.getrusage(resource.RUSAGE_SELF).ru_utime
                        + resource.getrusage(resource.RUSAGE_SELF).ru_stime
                    ),
                    "sklearn_version": sklearn.__version__,
                    "python_version": sys.version.split()[0],
                    "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
                    "joblib_backend": "threading",
                    "repeat_prediction_max_abs_delta": stability["max_abs_delta"],
                },
                "robustness_checks": robustness,
                "environment_contract": {
                    "api_key_environment_present": any(
                        "KEY" in key or "TOKEN" in key for key in os.environ
                    ),
                    "validation_labels_received": False,
                    "test_received": False,
                },
            },
        )
        return 0
    except Exception as error:
        # Error text may contain the model source's parameter names, never API
        # credentials (the worker environment and request do not contain them).
        _save_json(
            output_path,
            {
                "error": {"type": type(error).__name__, "message": str(error)[:3000]},
                "resources": {
                    "worker_wall_seconds": time.perf_counter() - started,
                    "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                },
            },
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
