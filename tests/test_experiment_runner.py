"""Offline matrix/aggregation tests: these tests never call a remote provider."""

import importlib.util
import json
from pathlib import Path

import pytest

from capability_factory.contracts import RunRequest
from capability_factory.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "experiment_runner", ROOT / "scripts/run_experiments.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CASES = MODULE.load_cases(ROOT / "examples/task_cases.json")


def test_smoke_and_full_matrix_use_exact_profiles():
    smoke = MODULE.build_plan(CASES)
    full = MODULE.build_plan(CASES, suite="full")
    assert smoke["planned_runs"] == 8
    assert smoke["selected_case_ids"] == ["B01", "S01"]
    assert full["planned_runs"] == 48
    assert MODULE.build_plan(CASES, suite="full", repeats=2)["planned_runs"] == 96
    for job in full["jobs"]:
        request = RunRequest.model_validate(job["request"])
        assert request.provider == "mock"
        if job["profile"] == "A":
            assert not request.use_retrieval and not request.use_graph
            assert request.max_candidates == 1 and request.max_repairs == 0
        elif job["profile"] == "B":
            assert request.use_retrieval and not request.use_graph
            assert request.max_candidates == 1 and request.max_repairs == 0
        elif job["profile"] == "C":
            assert request.use_retrieval and request.use_graph
            assert request.max_candidates == 1 and request.max_repairs == 2
        else:
            assert request.use_retrieval and request.use_graph
            assert request.max_candidates == 6 and request.max_repairs == 2
            assert request.orchestration == "multi_role" and request.search == "beam"
        if job["profile"] != "D":
            assert request.orchestration == "single_shot"


def test_filters_and_matrix_fingerprint_are_reproducible():
    first = MODULE.build_plan(CASES, profiles=["D", "B"], case_ids=["S02", "B03"], repeats=2)
    second = MODULE.build_plan(CASES, profiles=["B", "D"], case_ids=["B03", "S02"], repeats=2)
    assert first["planned_runs"] == 8
    assert first["matrix_sha256"] == second["matrix_sha256"]
    assert first["experiment_id"] != second["experiment_id"]
    assert len({job["run_id"] for job in first["jobs"]}) == 8
    assert first["selected_case_ids"] == ["B03", "S02"]
    assert first["jobs"][0]["profile"] != first["jobs"][2]["profile"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"repeats": 0},
        {"repeats": True},
        {"profiles": ["Z"]},
        {"profiles": ["A", "A"]},
        {"case_ids": ["missing"]},
        {"case_ids": ["B01", "B01"]},
    ],
)
def test_invalid_matrix_requests_are_rejected(kwargs):
    with pytest.raises(ValueError):
        MODULE.build_plan(CASES, **kwargs)


def _report(run_id, *, status="passed", ap=0.8, usage=None):
    return {
        "run_id": run_id,
        "status": status,
        "finished_at": "2026-09-28T00:00:00+00:00",
        "provider": "mock",
        "mode": "mock",
        "model": "deterministic-mock-v1",
        "timing": {"wall_seconds": 2.5},
        "usage": usage
        if usage is not None
        else {"calls": 3, "input_tokens": 0, "output_tokens": 0},
        "selected_candidate_id": "c1" if status == "passed" else None,
        "candidates": [
            {
                "candidate_id": "c1",
                "status": status,
                "plan": {"algorithm": "logistic"},
                "metrics": {"average_precision": ap} if ap is not None else {},
                "repairs": [],
                "attempts": [{}],
            }
        ],
    }


def test_summary_excludes_unstarted_and_missing_scores():
    plan = MODULE.build_plan(CASES, provider="deepseek")
    passed_job, failed_job = plan["jobs"][:2]
    passed = MODULE.observed_record(
        passed_job,
        _report(passed_job["run_id"], usage={"calls": 3, "input_tokens": 100, "output_tokens": 20}),
        3.0,
    )
    failed = MODULE.observed_record(
        failed_job, _report(failed_job["run_id"], status="failed", ap=None, usage={}), 4.0
    )
    summary = MODULE.summarize(plan, [passed, failed])
    assert summary["planned_runs"] == 8
    assert summary["unstarted_runs"] == 6
    assert summary["totals"]["completed_runs"] == 2
    assert summary["totals"]["passed_runs"] == 1
    assert summary["totals"]["failed_runs"] == 1
    assert summary["totals"]["observed_input_tokens"] == 100
    assert summary["totals"]["usage_missing_runs"] == 1
    assert summary["totals"]["mean_selected_validation_ap"] == 0.8
    assert summary["totals"]["sample_std_selected_validation_ap"] is None
    assert summary["totals"]["pass_rate_completed"] == 0.5


def test_summary_rejects_duplicate_observations_and_keeps_nan_missing():
    plan = MODULE.build_plan(CASES)
    job = plan["jobs"][0]
    row = MODULE.observed_record(job, _report(job["run_id"], ap=float("nan")), 1.0)
    assert row["selected_average_precision"] is None
    assert row["candidate_results"][0]["metrics"]["average_precision"] is None
    assert MODULE.summarize(plan, [row])["totals"]["scored_passed_runs"] == 0
    with pytest.raises(ValueError, match="unique planned jobs"):
        MODULE.summarize(plan, [row, row])


def test_summary_does_not_average_ap_across_different_datasets():
    plan = MODULE.build_plan(CASES, profiles=["A"])
    rows = [
        MODULE.observed_record(job, _report(job["run_id"], ap=ap), 1.0)
        for job, ap in zip(plan["jobs"], [0.18, 0.96])
    ]
    summary = MODULE.summarize(plan, rows)
    assert summary["totals"]["scored_passed_runs"] == 2
    assert summary["totals"]["mean_selected_validation_ap"] is None
    assert summary["totals"]["sample_std_selected_validation_ap"] is None
    assert summary["totals"]["metric_aggregation"] == "not_combined_across_datasets"
    assert [group["mean_selected_validation_ap"] for group in summary["by_profile_dataset"]] == [
        0.18,
        0.96,
    ]


def test_dry_run_writes_plan_and_zero_observations_without_workflows(tmp_path):
    plan = MODULE.build_plan(CASES)
    settings = Settings(root=ROOT, api_key="test-secret-never-serialize")

    def forbidden_factory(*args, **kwargs):
        raise AssertionError("Dry run must never create a workflow")

    output = tmp_path / "dry"
    summary = MODULE.run_matrix(
        plan, settings, output, dry_run=True, workflow_factory=forbidden_factory
    )
    assert (output / "plan.json").is_file()
    assert (output / "summary.json").is_file()
    assert (output / "summary.csv").is_file()
    assert not (output / "results.jsonl").exists()
    assert summary["totals"]["completed_runs"] == 0
    assert summary["unstarted_runs"] == 8
    assert "test-secret-never-serialize" not in (output / "plan.json").read_text()
    assert not (output / "databases").exists()


def test_matrix_preregisters_isolates_stores_and_records_actual_results(tmp_path):
    output = tmp_path / "matrix"
    plan = MODULE.build_plan(CASES, profiles=["A", "B"], case_ids=["B01"])
    paths = []

    class OfflineWorkflow:
        def __init__(self, settings, store):
            assert (output / "plan.json").exists(), "Plan must precede calls"
            paths.append(store.db_path)

        def run(self, request, run_id):
            assert request.provider == "mock"
            return _report(run_id, ap=0.8 if not request.use_retrieval else 0.9)

    summary = MODULE.run_matrix(plan, Settings(root=ROOT), output, workflow_factory=OfflineWorkflow)
    assert len(set(paths)) == 2
    assert all(str(output / "databases") in path for path in paths)
    assert summary["totals"]["completed_runs"] == 2
    assert summary["totals"]["passed_runs"] == 2
    assert summary["totals"]["observed_api_calls"] == 0
    rows = [json.loads(line) for line in (output / "results.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["candidate_results"][0]["metrics"]["average_precision"] == 0.8
    assert summary["totals"]["mean_selected_validation_ap"] == pytest.approx(0.85)
    assert summary["totals"]["sample_std_selected_validation_ap"] > 0
    with pytest.raises(FileExistsError):
        MODULE.run_matrix(plan, Settings(root=ROOT), output, workflow_factory=OfflineWorkflow)


def test_harness_errors_do_not_become_completed_runs_or_expose_exception_secrets(tmp_path):
    class FailingWorkflow:
        def __init__(self, settings, store):
            pass

        def run(self, request, run_id):
            raise RuntimeError("test-sensitive-exception-text")

    output = tmp_path / "failure"
    plan = MODULE.build_plan(CASES, profiles=["A"], case_ids=["B01"])
    summary = MODULE.run_matrix(plan, Settings(root=ROOT), output, workflow_factory=FailingWorkflow)
    assert summary["totals"]["completed_runs"] == 0
    assert summary["totals"]["harness_error_runs"] == 1
    assert summary["totals"]["mean_selected_validation_ap"] is None
    assert "test-sensitive-exception-text" not in (output / "results.jsonl").read_text()


def test_interrupt_retains_observations_and_leaves_remaining_runs_unstarted(tmp_path):
    class InterruptingWorkflow:
        def __init__(self, settings, store):
            pass

        def run(self, request, run_id):
            raise KeyboardInterrupt

    plan = MODULE.build_plan(CASES)
    output = tmp_path / "interrupt"
    summary = MODULE.run_matrix(
        plan, Settings(root=ROOT), output, workflow_factory=InterruptingWorkflow
    )
    assert summary["totals"]["completed_runs"] == 0
    assert summary["totals"]["attempted_runs"] == 1
    assert summary["unstarted_runs"] == 7
    assert summary["status_counts"] == {"interrupted": 1}
