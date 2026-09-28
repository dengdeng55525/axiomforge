"""Run a preregistered, isolated A/B/C/D workflow matrix with honest summaries.

Examples (real calls are billable and are never a fallback for mock):
  .venv/bin/python scripts/run_experiments.py --provider mock --suite smoke
  .venv/bin/python scripts/run_experiments.py --provider deepseek --suite full --dry-run
  .venv/bin/python scripts/run_experiments.py --provider deepseek --case-ids B01,S01 --profiles A,D

plan.json is written before any Workflow call. Each job starts with a fresh
knowledge database to prevent earlier runs' writeback from contaminating later
profiles. Runtime settings use the ordinary private .env/environment loader,
but only an explicit non-secret settings allowlist is recorded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import statistics
import subprocess
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

PROFILES = {
    "A": {
        "use_retrieval": False,
        "use_graph": False,
        "orchestration": "single_shot",
        "max_candidates": 1,
        "max_repairs": 0,
        "search": "compare",
    },
    "B": {
        "use_retrieval": True,
        "use_graph": False,
        "orchestration": "single_shot",
        "max_candidates": 1,
        "max_repairs": 0,
        "search": "compare",
    },
    "C": {
        "use_retrieval": True,
        "use_graph": True,
        "orchestration": "single_shot",
        "max_candidates": 1,
        "max_repairs": 2,
        "search": "compare",
    },
    "D": {
        "use_retrieval": True,
        "use_graph": True,
        "orchestration": "multi_role",
        "max_candidates": 6,
        "max_repairs": 2,
        "search": "beam",
    },
}
LIMITATIONS = [
    "Only actual terminal workflow reports count as completed runs; planned/unstarted jobs are not observations.",
    "Mock results test software behavior and CPU estimators, not DeepSeek capability or API cost.",
    "One repeat cannot establish statistical reliability; sample standard deviations require at least two observations.",
    "Cases reuse the same fixed train/validation splits and are correlated, not independent dataset samples.",
    "Candidate selection uses validation AP; the sealed final test remains unscored, so selection bias remains.",
    "A/B/C/D change multiple mechanisms across some comparisons; C versus B and D versus C are not single-factor causal ablations.",
    "Temperature zero and fixed estimator seeds do not guarantee identical remote LLM responses or hardware timings.",
    "Case expected_outcome labels are retained for review, not automatically equated with workflow status or semantic task success.",
    "No faults are injected in the base matrix; repair statistics only describe failures that actually occurred.",
    "Each job gets the same source-derived initial knowledge and its own database; cross-run learning is deliberately excluded.",
    "Provider token totals are reported observations, not a billing reconciliation; failures without usage remain missing.",
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def load_cases(path: Path) -> list[dict]:
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = content["cases"]
    seen = set()
    for case in cases:
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("id"), str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", case["id"])
            or case["id"] in seen
            or case.get("dataset") not in {"bank", "sms"}
            or not isinstance(case.get("prompt"), str)
            or len(case["prompt"]) < 5
            or not isinstance(case.get("expected"), str)
        ):
            raise ValueError(
                "Case file must have unique IDs, bank/sms datasets, prompts and expected outcomes"
            )
        seen.add(case["id"])
    return cases


def build_plan(
    cases: list[dict],
    *,
    provider: str = "mock",
    suite: str = "smoke",
    repeats: int = 1,
    profiles: list[str] | None = None,
    case_ids: list[str] | None = None,
) -> dict:
    from capability_factory.contracts import RunRequest

    if provider not in {"mock", "deepseek"} or suite not in {"smoke", "full"}:
        raise ValueError("Unsupported provider or suite")
    if type(repeats) is not int or not 1 <= repeats <= 100:
        raise ValueError("repeats must be an integer between 1 and 100")
    requested_profiles = profiles or list(PROFILES)
    if len(set(requested_profiles)) != len(requested_profiles) or not set(
        requested_profiles
    ) <= set(PROFILES):
        raise ValueError("Profiles must be unique members of A,B,C,D")
    selected_profiles = [name for name in PROFILES if name in requested_profiles]
    known_ids = {case["id"] for case in cases}
    if case_ids is not None:
        if not case_ids or len(set(case_ids)) != len(case_ids) or not set(case_ids) <= known_ids:
            raise ValueError("case-ids must be unique IDs present in the case file")
        chosen = [case for case in cases if case["id"] in case_ids]
    elif suite == "smoke":
        chosen = []
        for dataset in ("bank", "sms"):
            match = next((case for case in cases if case["dataset"] == dataset), None)
            if match is None:
                raise ValueError("Smoke suite requires one bank and one SMS case")
            chosen.append(match)
    else:
        chosen = list(cases)
    if not chosen or not selected_profiles:
        raise ValueError("Experiment matrix cannot be empty")
    experiment_id = uuid.uuid4().hex
    jobs = []
    for repeat in range(1, repeats + 1):
        for case_index, case in enumerate(chosen):
            offset = (case_index + repeat - 1) % len(selected_profiles)
            order = selected_profiles[offset:] + selected_profiles[:offset]
            for profile in order:
                job_id = f"{profile}_{case['id']}_r{repeat:02d}"
                request = RunRequest(
                    description=case["prompt"],
                    dataset_id=case["dataset"],
                    provider=provider,
                    **PROFILES[profile],
                )
                jobs.append(
                    {
                        "job_id": job_id,
                        "profile": profile,
                        "case_id": case["id"],
                        "dataset": case["dataset"],
                        "repeat": repeat,
                        "expected_outcome": case["expected"],
                        "run_id": uuid.uuid5(uuid.UUID(experiment_id), job_id).hex,
                        "request": request.model_dump(),
                    }
                )
    fingerprint = [{key: value for key, value in job.items() if key != "run_id"} for job in jobs]
    return {
        "schema_version": "1.0",
        "experiment_id": experiment_id,
        "created_at": _now(),
        "provider": provider,
        "suite": suite,
        "repeats": repeats,
        "profiles": {name: PROFILES[name].copy() for name in selected_profiles},
        "selected_case_ids": [case["id"] for case in chosen],
        "case_selection": "explicit_filter" if case_ids is not None else suite,
        "planned_runs": len(jobs),
        "jobs": jobs,
        "matrix_sha256": hashlib.sha256(
            json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "ordering": "deterministic profile rotation by case and repeat",
        "knowledge_policy": "fresh isolated database per job; identical source-derived initial knowledge",
        "statistical_limitations": LIMITATIONS.copy(),
    }


def _number(value):
    return value if type(value) in {int, float} and math.isfinite(value) else None


def _clean_observations(value):
    if isinstance(value, dict):
        return {key: _clean_observations(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_observations(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def observed_record(job: dict, report: dict, elapsed: float) -> dict:
    candidates = report.get("candidates") or []
    selected = next(
        (
            item
            for item in candidates
            if item.get("candidate_id") == report.get("selected_candidate_id")
        ),
        None,
    )
    usage = report.get("usage") or {}
    provider = job["request"]["provider"]
    status = report.get("status", "unknown")
    completed = status in {"passed", "failed", "cancelled"} and bool(report.get("finished_at"))
    candidate_rows = [
        {
            "candidate_id": item.get("candidate_id"),
            "status": item.get("status"),
            "algorithm": (item.get("plan") or {}).get("algorithm"),
            "actual_algorithm": (item.get("model_metadata") or {}).get("actual_algorithm"),
            "metrics": _clean_observations(item.get("metrics") or {}),
            "resources": _clean_observations(item.get("resources") or {}),
            "repair_attempts": len(item.get("repairs") or []),
            "validation_attempts": len(item.get("attempts") or []),
        }
        for item in candidates
    ]
    metrics = (selected.get("metrics") or {}) if selected else {}
    return {
        **{
            key: job[key]
            for key in ("job_id", "profile", "case_id", "dataset", "repeat", "expected_outcome")
        },
        "provider": provider,
        "mode": report.get("mode"),
        "model": report.get("model"),
        "run_id": report.get("run_id", job["run_id"]),
        "status": status,
        "workflow_completed": completed,
        "recorded_at": _now(),
        "finished_at": report.get("finished_at"),
        "workflow_wall_seconds": _number((report.get("timing") or {}).get("wall_seconds")),
        "harness_wall_seconds": elapsed,
        "llm_role_calls": _number(usage.get("calls")),
        "api_calls": _number(usage.get("calls")) if provider == "deepseek" else 0,
        "input_tokens": _number(usage.get("input_tokens")),
        "output_tokens": _number(usage.get("output_tokens")),
        "cached_input_tokens": _number(usage.get("cached_input_tokens")),
        "selected_candidate_id": report.get("selected_candidate_id"),
        "selected_average_precision": _number(metrics.get("average_precision")),
        "selected_roc_auc": _number(metrics.get("roc_auc")),
        "selected_lift_at_10pct": _number(metrics.get("lift_at_10pct")),
        "selected_quality_status": selected.get("quality_status") if selected else None,
        "candidate_count": len(candidates),
        "passed_candidate_count": sum(item.get("status") == "passed" for item in candidates),
        "repair_attempts": sum(item["repair_attempts"] for item in candidate_rows),
        "candidate_results": candidate_rows,
        "report_paths": report.get("report_paths") or {},
        "semantic_expected_outcome_checked": False,
    }


def _group_summary(rows: list[dict]) -> dict:
    completed = [row for row in rows if row.get("workflow_completed")]
    passed = [row for row in completed if row.get("status") == "passed"]
    aps = [
        row["selected_average_precision"]
        for row in passed
        if _number(row.get("selected_average_precision")) is not None
    ]
    comparable_dataset = len({row["dataset"] for row in passed}) <= 1
    output = {
        "attempted_runs": len(rows),
        "completed_runs": len(completed),
        "passed_runs": len(passed),
        "failed_runs": sum(row.get("status") == "failed" for row in completed),
        "cancelled_runs": sum(row.get("status") == "cancelled" for row in completed),
        "harness_error_runs": sum(row.get("status") == "harness_error" for row in rows),
        "pass_rate_completed": len(passed) / len(completed) if completed else None,
        "scored_passed_runs": len(aps),
        "mean_selected_validation_ap": statistics.mean(aps) if aps and comparable_dataset else None,
        "sample_std_selected_validation_ap": statistics.stdev(aps)
        if len(aps) > 1 and comparable_dataset
        else None,
        "metric_aggregation": "within_single_dataset"
        if comparable_dataset
        else "not_combined_across_datasets",
        "usage_missing_runs": sum(
            row.get("input_tokens") is None or row.get("output_tokens") is None for row in rows
        ),
    }
    for field in (
        "api_calls",
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "workflow_wall_seconds",
        "harness_wall_seconds",
        "repair_attempts",
    ):
        known = [row[field] for row in rows if _number(row.get(field)) is not None]
        output["observed_" + field] = sum(known)
        output[field + "_observed_runs"] = len(known)
    return output


def summarize(plan: dict, records: list[dict]) -> dict:
    valid_job_ids = {job["job_id"] for job in plan["jobs"]}
    seen = set()
    for record in records:
        identity = record.get("job_id")
        if identity not in valid_job_ids or identity in seen:
            raise ValueError("Summary records must identify unique planned jobs")
        seen.add(identity)
    groups = []
    for profile in plan["profiles"]:
        for dataset in sorted({job["dataset"] for job in plan["jobs"]}):
            rows = [
                row for row in records if row["profile"] == profile and row["dataset"] == dataset
            ]
            planned = sum(
                job["profile"] == profile and job["dataset"] == dataset for job in plan["jobs"]
            )
            if planned:
                groups.append(
                    {
                        "profile": profile,
                        "dataset": dataset,
                        "planned_runs": planned,
                        **_group_summary(rows),
                    }
                )
    return {
        "schema_version": "1.0",
        "experiment_id": plan["experiment_id"],
        "provider": plan["provider"],
        "updated_at": _now(),
        "planned_runs": plan["planned_runs"],
        "unstarted_runs": plan["planned_runs"] - len(records),
        "totals": _group_summary(records),
        "status_counts": dict(Counter(row["status"] for row in records)),
        "by_profile_dataset": groups,
        "statistical_limitations": plan["statistical_limitations"],
    }


def _write_summaries(output: Path, plan: dict, records: list[dict]) -> dict:
    summary = summarize(plan, records)
    _write_json(output / "summary.json", summary)
    groups = summary["by_profile_dataset"]
    with (output / "summary.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(groups[0]))
        writer.writeheader()
        writer.writerows(groups)
    return summary


def _safe_invocation(settings, plan: dict, dry_run: bool) -> dict:
    versions = {}
    for name in ("scikit-learn", "numpy", "pandas", "pydantic", "httpx"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    revision, dirty = None, None
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=settings.root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if probe.returncode == 0:
            revision = probe.stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=settings.root,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            dirty = bool(status.stdout.strip()) if status.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        pass
    code_hashes = {}
    for relative in (
        "scripts/run_experiments.py",
        "src/capability_factory/workflow.py",
        "src/capability_factory/providers.py",
        "src/capability_factory/prompts.py",
        "src/capability_factory/contracts.py",
        "src/capability_factory/datasets.py",
        "src/capability_factory/metrics.py",
        "src/capability_factory/knowledge.py",
        "src/capability_factory/execution/compiler.py",
        "src/capability_factory/execution/worker.py",
        "src/capability_factory/execution/runner.py",
    ):
        path = settings.root / relative
        if path.is_file():
            code_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "project_root": str(settings.root),
        "provider": plan["provider"],
        "model": "deterministic-mock-v1" if plan["provider"] == "mock" else settings.model,
        "suite": plan["suite"],
        "repeats": plan["repeats"],
        "dry_run": dry_run,
        "request_timeout_s": settings.request_timeout_s,
        "per_run_limits": {
            "max_calls": settings.max_calls,
            "max_input_tokens": settings.max_input_tokens,
            "max_output_tokens": settings.max_output_tokens,
        },
        "python_version": platform.python_version(),
        "package_versions": versions,
        "git_revision": revision,
        "git_worktree_dirty": dirty,
        "source_sha256": code_hashes,
        "credentials_recorded": False,
    }


def run_matrix(
    plan: dict, settings, output: Path, *, dry_run: bool = False, workflow_factory=None
) -> dict:
    from capability_factory.contracts import RunRequest
    from capability_factory.knowledge import KnowledgeStore
    from capability_factory.workflow import Workflow

    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Experiment output directory is not empty; choose a fresh directory")
    output.mkdir(parents=True, exist_ok=True)
    plan = dict(plan)
    plan["invocation"] = _safe_invocation(settings, plan, dry_run)
    plan["case_source_sha256"] = hashlib.sha256(
        (settings.root / "examples/task_cases.json").read_bytes()
    ).hexdigest()
    _write_json(output / "plan.json", plan)
    records = []
    summary = _write_summaries(output, plan, records)
    if dry_run:
        return summary
    factory = workflow_factory or Workflow
    with (output / "results.jsonl").open("a", encoding="utf-8") as observations:
        for job in plan["jobs"]:
            started = time.monotonic()
            store = KnowledgeStore(output / "databases" / (job["job_id"] + ".sqlite3"))
            interrupted = False
            try:
                workflow = factory(settings, store=store)
                report = workflow.run(
                    RunRequest.model_validate(job["request"]), run_id=job["run_id"]
                )
                record = observed_record(job, report, time.monotonic() - started)
            except (Exception, KeyboardInterrupt) as error:
                interrupted = isinstance(error, KeyboardInterrupt)
                record = observed_record(
                    job,
                    {"status": "interrupted" if interrupted else "harness_error"},
                    time.monotonic() - started,
                )
                record["harness_error_type"] = type(error).__name__
                # Arbitrary exception messages can contain request credentials.
                record["harness_error_message"] = (
                    "Workflow did not return a terminal report; raw exception intentionally omitted"
                )
            finally:
                store.close()
            records.append(record)
            observations.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            observations.flush()
            summary = _write_summaries(output, plan, records)
            print(
                json.dumps(
                    {
                        "job_id": job["job_id"],
                        "status": record["status"],
                        "completed_runs": summary["totals"]["completed_runs"],
                        "planned_runs": plan["planned_runs"],
                    }
                ),
                flush=True,
            )
            if interrupted:
                break
    return summary


def main(argv=None) -> int:
    from capability_factory.settings import load_settings

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["mock", "deepseek"], default="mock")
    parser.add_argument("--suite", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profiles", default="A,B,C,D")
    parser.add_argument("--case-ids")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        cases = load_cases(ROOT / "examples/task_cases.json")
        plan = build_plan(
            cases,
            provider=args.provider,
            suite=args.suite,
            repeats=args.repeats,
            profiles=[item.strip() for item in args.profiles.split(",")],
            case_ids=[item.strip() for item in args.case_ids.split(",")] if args.case_ids else None,
        )
        settings = load_settings(ROOT)
        output = args.output or (
            ROOT
            / "artifacts/experiments"
            / (
                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                + "-"
                + plan["experiment_id"][:8]
            )
        )
        summary = run_matrix(plan, settings, output, dry_run=args.dry_run)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "planned_runs": summary["planned_runs"],
                "completed_runs": summary["totals"]["completed_runs"],
                "passed_runs": summary["totals"]["passed_runs"],
                "unstarted_runs": summary["unstarted_runs"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if args.dry_run or summary["totals"]["passed_runs"] == summary["planned_runs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
