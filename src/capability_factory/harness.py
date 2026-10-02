"""Offline, trace-based Agent evaluation harness.

The harness is deliberately local and deterministic.  It evaluates a persisted
AxiomForge report against a versioned case rubric, builds a cursor-safe trace
projection, and emits evidence for every check.  It never calls a model,
executes generated code, or writes to the knowledge store.  This gives the
project a small modern-agent evaluation layer without requiring a hosted
tracing vendor or a network connection.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from capability_factory.observability import build_agent_trace

HARNESS_SCHEMA_VERSION = "agent-harness.v1"
_CASE_ID = re.compile(r"^[a-z][a-z0-9_.-]{1,63}$")
_EVENT = re.compile(r"^[A-Z][A-Z0-9_.-]{1,79}$")


class HarnessCase(BaseModel):
    """A reproducible rubric for one Agent run contract."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=2, max_length=64, pattern=_CASE_ID.pattern)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    dataset_id: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    required_event_types: list[str] = Field(default_factory=list, max_length=40)
    required_roles: list[str] = Field(default_factory=list, max_length=20)
    required_candidate_count: int = Field(default=1, ge=0, le=6)
    expected_statuses: list[str] = Field(default_factory=lambda: ["passed"], max_length=6)
    min_average_precision: float | None = Field(default=None, ge=0, le=1)
    min_candidate_average_precision: float | None = Field(default=None, ge=0, le=1)
    require_selected_candidate: bool = True
    require_repair_evidence: bool = False
    max_repair_attempts: int | None = Field(default=None, ge=0, le=20)
    max_wall_seconds: float | None = Field(default=None, gt=0, le=86400)
    forbid_event_data_keys: list[str] = Field(default_factory=lambda: ["prompt", "system", "api_key"], max_length=30)

    def model_post_init(self, __context: Any) -> None:
        for event_type in self.required_event_types:
            if not _EVENT.fullmatch(event_type):
                raise ValueError(f"invalid event type: {event_type}")
        for expected in self.expected_statuses:
            if expected not in {"passed", "completed", "failed", "cancelled", "rejected", "running"}:
                raise ValueError(f"invalid expected status: {expected}")


class HarnessCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    title: str
    passed: bool
    severity: str = "error"
    observed: Any = None
    expected: Any = None
    evidence: list[str] = Field(default_factory=list)


class HarnessResult(BaseModel):
    """Stable JSON contract consumed by CLI, API and the web workbench."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: str = HARNESS_SCHEMA_VERSION
    case_id: str
    run_id: str | None
    passed: bool
    score: float = Field(ge=0, le=1)
    checks: list[HarnessCheck]
    trace: dict[str, Any]
    summary: dict[str, Any]


def _default_cases_path(root: Path) -> Path:
    return root / "configs" / "agent_harness_cases.json"


def load_cases(path: Path) -> list[HarnessCase]:
    """Load and validate a bounded case file without importing executable code."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("cases") if isinstance(raw, dict) else raw
    if not isinstance(items, list) or len(items) > 100:
        raise ValueError("harness case file must contain at most 100 cases")
    cases = [HarnessCase.model_validate(item) for item in items]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("harness case IDs must be unique")
    return cases


def _check(
    checks: list[HarnessCheck], check_id: str, title: str, passed: bool, *,
    observed: Any = None, expected: Any = None, evidence: list[str] | None = None,
    severity: str = "error",
) -> None:
    checks.append(HarnessCheck(id=check_id, title=title, passed=bool(passed), severity=severity,
                               observed=observed, expected=expected, evidence=evidence or []))


def evaluate_report(report: dict[str, Any], case: HarnessCase) -> HarnessResult:
    """Evaluate one persisted report using only facts already in that report."""
    source = report if isinstance(report, dict) else {}
    checks: list[HarnessCheck] = []
    events = source.get("events") if isinstance(source.get("events"), list) else []
    event_types = [item.get("event_type", item.get("type")) for item in events if isinstance(item, dict)]
    event_types = [value for value in event_types if isinstance(value, str)]
    trace = build_agent_trace(source)
    status = source.get("status")
    run_id = source.get("run_id") if isinstance(source.get("run_id"), str) else None
    candidates = source.get("candidates") if isinstance(source.get("candidates"), list) else []
    selected_id = source.get("selected_candidate_id")
    selected = next((item for item in candidates if isinstance(item, dict) and item.get("candidate_id") == selected_id), None)

    _check(checks, "terminal_status", "运行达到预期终态", status in case.expected_statuses,
           observed=status, expected=case.expected_statuses, evidence=["report.status"])
    _check(checks, "dataset_contract", "数据集符合用例", case.dataset_id is None or source.get("dataset_id") == case.dataset_id,
           observed=source.get("dataset_id"), expected=case.dataset_id, evidence=["report.dataset_id"])
    missing_events = [name for name in case.required_event_types if name not in event_types]
    _check(checks, "workflow_events", "工作流事件完整", not missing_events,
           observed=sorted(set(event_types)), expected=case.required_event_types,
           evidence=[f"events.{name}" for name in case.required_event_types if name in event_types])
    roles = sorted({span.get("role") for span in trace.get("spans", []) if isinstance(span, dict) and span.get("role")})
    missing_roles = [role for role in case.required_roles if role not in roles]
    _check(checks, "agent_roles", "角色协作链完整", not missing_roles,
           observed=roles, expected=case.required_roles, evidence=[f"trace.spans[{role}]" for role in roles])
    _check(checks, "candidate_count", "候选方案达到用例要求", len(candidates) >= case.required_candidate_count,
           observed=len(candidates), expected=f">={case.required_candidate_count}", evidence=["report.candidates"])
    _check(checks, "selected_candidate", "存在已选择候选", not case.require_selected_candidate or bool(selected_id),
           observed=selected_id, expected="non-empty candidate id", evidence=["report.selected_candidate_id"])

    metrics = selected.get("metrics", {}) if isinstance(selected, dict) else {}
    observed_ap = metrics.get("average_precision") if isinstance(metrics, dict) else None
    min_ap = case.min_average_precision
    _check(checks, "selected_ap", "选中候选达到 AP 门槛", min_ap is None or (isinstance(observed_ap, (int, float)) and observed_ap >= min_ap),
           observed=observed_ap, expected=min_ap if min_ap is not None else "not configured",
           evidence=["selected_candidate.metrics.average_precision"], severity="warning" if min_ap is None else "error")
    candidate_aps = [item.get("metrics", {}).get("average_precision") for item in candidates
                     if isinstance(item, dict) and isinstance(item.get("metrics"), dict)
                     and isinstance(item["metrics"].get("average_precision"), (int, float))]
    min_candidate_ap = case.min_candidate_average_precision
    _check(checks, "candidate_ap", "至少一个候选达到 AP 门槛", min_candidate_ap is None or any(value >= min_candidate_ap for value in candidate_aps),
           observed=candidate_aps, expected=min_candidate_ap if min_candidate_ap is not None else "not configured",
           evidence=["report.candidates[*].metrics.average_precision"], severity="warning" if min_candidate_ap is None else "error")

    repairs = [item for candidate in candidates if isinstance(candidate, dict)
               for item in (candidate.get("repairs") if isinstance(candidate.get("repairs"), list) else [])]
    attempts = [item for candidate in candidates if isinstance(candidate, dict)
                for item in (candidate.get("attempts") if isinstance(candidate.get("attempts"), list) else [])]
    if case.require_repair_evidence:
        repair_ok = bool(repairs) and any(item.get("after_hash") for item in repairs if isinstance(item, dict))
    else:
        repair_ok = True
    _check(checks, "repair_evidence", "修复过程具备可验证证据", repair_ok,
           observed={"repairs": len(repairs), "attempts": len(attempts)}, expected="repair evidence" if case.require_repair_evidence else "not configured",
           evidence=["report.candidates[*].repairs"], severity="warning" if not case.require_repair_evidence else "error")
    if case.max_repair_attempts is not None:
        repair_limit_ok = len(repairs) <= case.max_repair_attempts
        _check(checks, "repair_budget", "修复次数不超过预算", repair_limit_ok,
               observed=len(repairs), expected=f"<={case.max_repair_attempts}", evidence=["report.candidates[*].repairs"])

    wall = source.get("timing", {}).get("wall_seconds") if isinstance(source.get("timing"), dict) else None
    wall_ok = case.max_wall_seconds is None or (isinstance(wall, (int, float)) and wall <= case.max_wall_seconds)
    _check(checks, "wall_budget", "运行耗时符合用例预算", wall_ok,
           observed=wall, expected=case.max_wall_seconds if case.max_wall_seconds is not None else "not configured",
           evidence=["report.timing.wall_seconds"], severity="warning" if case.max_wall_seconds is None else "error")

    forbidden: list[str] = []
    for index, event in enumerate(events):
        data = event.get("data") if isinstance(event, dict) and isinstance(event.get("data"), dict) else {}
        for key in case.forbid_event_data_keys:
            if key in data:
                forbidden.append(f"events[{index}].data.{key}")
    _check(checks, "trace_redaction", "事件记录未携带禁止字段", not forbidden,
           observed=forbidden, expected="empty", evidence=forbidden[:10] or ["events[*].data"])

    hard_checks = [item for item in checks if item.severity == "error"]
    passed = all(item.passed for item in hard_checks)
    score = round(sum(item.passed for item in checks) / len(checks), 4) if checks else 0.0
    return HarnessResult(
        case_id=case.id, run_id=run_id, passed=passed, score=score, checks=checks, trace=trace,
        summary={"status": status, "event_count": len(events), "candidate_count": len(candidates),
                 "roles": roles, "missing_events": missing_events, "missing_roles": missing_roles,
                 "repair_count": len(repairs), "attempt_count": len(attempts), "wall_seconds": wall,
                 "hard_checks": len(hard_checks), "hard_passed": sum(item.passed for item in hard_checks)},
    )


def evaluate_run(store: Any, run_id: str, case: HarnessCase) -> HarnessResult:
    """Read one report through the existing store; no writes are performed."""
    report = store.get_run(run_id)
    if report is None:
        raise KeyError(run_id)
    return evaluate_report(report, case)


def evaluate_suite(report: dict[str, Any], cases: list[HarnessCase]) -> dict[str, Any]:
    """Evaluate a run against a case suite and return an aggregate contract."""
    results = [evaluate_report(report, case) for case in cases]
    scores = [result.score for result in results]
    failed = [result.case_id for result in results if not result.passed]
    return {
        "schema_version": "agent-harness-suite.v1",
        "run_id": report.get("run_id") if isinstance(report, dict) else None,
        "passed": not failed and bool(results),
        "score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "case_count": len(results),
        "passed_cases": len(results) - len(failed),
        "failed_case_ids": failed,
        "results": [result.model_dump(mode="json") for result in results],
    }


__all__ = ["HARNESS_SCHEMA_VERSION", "HarnessCase", "HarnessCheck", "HarnessResult",
           "evaluate_report", "evaluate_run", "evaluate_suite", "load_cases"]
