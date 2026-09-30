"""Pure, cursor-bounded Agent observability projections.

The persisted run report remains the source of truth. This module creates a
small replay view from event facts only; it never copies prompts, generated
code, or model reasoning into the projection.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

START_TYPES = {"AGENT_STARTED": "agent", "TOOL_STARTED": "tool"}
END_TYPES = {
    "AGENT_COMPLETED": "completed",
    "AGENT_REJECTED": "rejected",
    "AGENT_FAILED": "failed",
    "TOOL_COMPLETED": "completed",
    "TOOL_FAILED": "failed",
}
RESPONSE_TYPES = {"LLM_RESPONSE", "MOCK_RESPONSE"}
SAFE_LABEL = re.compile(r"^[A-Za-z0-9_.:/+-]{1,160}$")
SAFE_EVENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,99}$")
KNOWN_STATUSES = {"queued", "running", "finalizing", "completed", "passed", "failed", "cancelled", "rejected"}


def _safe_label(value: Any, *, event: bool = False) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    pattern = SAFE_EVENT if event else SAFE_LABEL
    if "://" in candidate or candidate.lower().startswith(("sk-", "ghp_", "gho_", "github_pat_")):
        return None
    return candidate if pattern.fullmatch(candidate) else None


def _safe_timestamp(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) > 128:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    # A wall observation must have an explicit timezone to be independent of
    # the machine rendering this historical report.
    return value if stamp.tzinfo is not None else None


def _number(value: Any, *, integer: bool = False, minimum: float | None = None) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if integer and not isinstance(value, int):
        return None
    if minimum is not None and value < minimum:
        return None
    return value


def _safe_ids(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        safe = _safe_label(item)
        if safe and safe not in result:
            result.append(safe)
    return result


def _data(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("data")
    return value if isinstance(value, dict) else {}


def _event_type(event: dict[str, Any]) -> str | None:
    return _safe_label(event.get("event_type", event.get("type")), event=True)


def _status(event_type: str | None, data: dict[str, Any]) -> str | None:
    if event_type in START_TYPES:
        return "running"
    if event_type in END_TYPES:
        if data.get("status") == "cancelled" or _is_cancelled(data):
            return "cancelled"
        return END_TYPES[event_type]
    if event_type in {"CANCELLED", "RUN_CANCELLED"}:
        return "cancelled"
    if event_type in {"FAILED", "RUN_FAILED"}:
        return "failed"
    if event_type in {"COMPLETED", "RUN_COMPLETED"}:
        return "completed"
    if event_type == "RUN_FINISHED":
        declared = data.get("status")
        return declared if isinstance(declared, str) and declared in KNOWN_STATUSES else None
    return None


def _is_cancelled(data: dict[str, Any]) -> bool:
    value = data.get("error_type")
    return isinstance(value, str) and value.strip().lower() in {"cancelled", "canceled", "cancel"}


def _safe_event(event: dict[str, Any], event_type: str | None) -> dict[str, Any]:
    data = _data(event)
    result: dict[str, Any] = {
        "sequence": event.get("sequence"),
        "event_type": event_type or "unknown",
        "created_at": _safe_timestamp(event.get("created_at")),
    }
    for key in ("role", "span_id", "name", "error_type"):
        safe = _safe_label(data.get(key, event.get(key)), event=key in {"status", "error_type"})
        if safe is not None:
            result[key] = safe
    state = "cancelled" if _is_cancelled(data) else _status(event_type, data)
    if state:
        result["status"] = state
    elif isinstance(data.get("status"), str) and data["status"] in KNOWN_STATUSES:
        result["status"] = data["status"]
    return result


def _rows(report: dict[str, Any]) -> list[tuple[int, dict[str, Any], str | None]]:
    raw = report.get("events")
    if not isinstance(raw, list):
        return []
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        sequence = item.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            continue
        rows.append((sequence, item, _event_type(item)))
    counts = Counter(row[0] for row in rows)
    # Conflicting identities do not establish an order or a unique billed call.
    # Exclude every duplicate sequence instead of choosing an arbitrary winner.
    return sorted((row for row in rows if counts[row[0]] == 1), key=lambda row: row[0])


def _timestamp_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError):
        return None


def _limit(report: dict[str, Any], key: str) -> int | float | None:
    for source in (report.get("resource_budget"), report.get("request")):
        if isinstance(source, dict):
            value = _number(source.get(key), integer=key != "max_seconds", minimum=0)
            if value is not None:
                return value
    return None


def _budget(report: dict[str, Any], selected: list[tuple[int, dict[str, Any], str | None]], full: bool) -> dict[str, Any]:
    responses = [row for row in selected if row[2] in RESPONSE_TYPES]
    values = {key: [] for key in ("input_tokens", "output_tokens", "cached_input_tokens")}
    for _, event, event_type in responses:
        if event_type == "LLM_RESPONSE":
            data = _data(event)
            for key in values:
                value = _number(data.get(key), integer=True, minimum=0)
                values[key].append(value)
    calls = len(responses)
    report_usage = report.get("usage") if full and isinstance(report.get("usage"), dict) else {}
    usage: dict[str, Any] = {"calls": calls}
    for key, items in values.items():
        usage[key] = None if not items or any(value is None for value in items) else sum(items)
    # Final counters include transport retries which produce no LLM_RESPONSE.
    # Replay cursors never read these mutable final aggregates.
    usage_source = "events" if responses else "unavailable"
    for key in ("input_tokens", "output_tokens", "cached_input_tokens"):
        value = _number(report_usage.get(key), integer=True, minimum=0)
        if value is not None and usage[key] is None:
            usage[key] = value
            usage_source = "report"
    report_calls = _number(report_usage.get("calls"), integer=True, minimum=0)
    if report_calls is not None and report_calls >= usage["calls"]:
        if report_calls != usage["calls"]:
            usage_source = "report"
        usage["calls"] = report_calls
    max_seconds = _limit(report, "max_seconds")
    for _, event, event_type in selected:
        if event_type == "RUN_BUDGET_APPLIED":
            value = _number(_data(event).get("effective_seconds"), minimum=0)
            if value is not None:
                max_seconds = value
    wall_seconds = None
    if full and isinstance(report.get("timing"), dict):
        wall_seconds = _number(report["timing"].get("wall_seconds"), minimum=0)
    if wall_seconds is None:
        times = [_timestamp_seconds(_safe_timestamp(event.get("created_at"))) for _, event, _ in selected]
        times = [value for value in times if value is not None]
        if len(times) >= 2 and times[-1] >= times[0]:
            wall_seconds = round(times[-1] - times[0], 6)
    return {
        **usage,
        "max_calls": _limit(report, "max_calls"),
        "max_input_tokens": _limit(report, "max_input_tokens"),
        "max_output_tokens": _limit(report, "max_output_tokens"),
        "max_seconds": max_seconds,
        "wall_seconds": wall_seconds,
        "usage_source": usage_source,
    }


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    value = _number(data.get("returned_count"), integer=True, minimum=0)
    return {
        "result_keys": _safe_ids(data.get("result_keys")),
        "returned_count": value,
        "capability_ids": _safe_ids(data.get("capability_ids")),
    }


def _new_spans(selected: list[tuple[int, dict[str, Any], str | None]]) -> list[dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for sequence, event, event_type in selected:
        data = _data(event)
        if event_type in START_TYPES:
            span_id = _safe_label(data.get("span_id"))
            if span_id is None or span_id in active:
                continue
            span = {
                "span_id": span_id,
                "kind": START_TYPES[event_type],
                "name": _safe_label(data.get("name")),
                "role": _safe_label(data.get("role")),
                "status": "running",
                "attempt": _number(data.get("attempt"), integer=True, minimum=0),
                "candidate_id": _safe_label(data.get("candidate_id")),
                "started_at": _safe_timestamp(event.get("created_at")),
                "finished_at": None,
                "duration_seconds": None,
                "start_sequence": sequence,
                "end_sequence": None,
                "schema": _safe_label(data.get("schema")),
                "error_type": None,
                "output_summary": {"result_keys": [], "returned_count": None, "capability_ids": []},
                "model": _safe_label(data.get("model")),
            }
            active[span_id] = span
            order.append(span_id)
        elif event_type in END_TYPES:
            span_id = _safe_label(data.get("span_id"))
            span = active.get(span_id)
            expected_kind = "agent" if event_type.startswith("AGENT_") else "tool"
            if span is None or span["status"] != "running" or span["kind"] != expected_kind:
                continue
            span["status"] = "cancelled" if _is_cancelled(data) else (_status(event_type, data) or "failed")
            span["finished_at"] = _safe_timestamp(event.get("created_at"))
            span["end_sequence"] = sequence
            span["duration_seconds"] = _number(data.get("duration_seconds"), minimum=0)
            span["error_type"] = _safe_label(data.get("error_type"), event=True)
            span["output_summary"] = _summary(data)
            for key in ("name", "role", "candidate_id", "schema", "model"):
                value = _safe_label(data.get(key))
                if value is not None and span[key] is None:
                    span[key] = value
            attempt = _number(data.get("attempt"), integer=True, minimum=0)
            if attempt is not None and span["attempt"] is None:
                span["attempt"] = attempt
    return [active[span_id] for span_id in order]


def _legacy_spans(selected: list[tuple[int, dict[str, Any], str | None]]) -> list[dict[str, Any]]:
    spans = []
    for sequence, event, event_type in selected:
        data = _data(event)
        if event_type in RESPONSE_TYPES:
            role = _safe_label(data.get("role"))
            spans.append({
                "span_id": f"legacy-agent-{sequence}",
                "kind": "agent",
                "name": role or event_type.lower(),
                "role": role,
                "status": "completed",
                "attempt": None,
                "candidate_id": None,
                "started_at": None,
                "finished_at": _safe_timestamp(event.get("created_at")),
                "duration_seconds": _number(data.get("seconds"), minimum=0),
                "start_sequence": None,
                "end_sequence": sequence,
                "schema": None,
                "error_type": None,
                "output_summary": {"result_keys": [], "returned_count": None, "capability_ids": []},
                "source_event": event_type,
                "model": _safe_label(data.get("returned_model") or data.get("model")),
            })
        elif event_type == "KNOWLEDGE_RETRIEVED":
            ids = _safe_ids(data.get("capability_ids"))
            spans.append({
                "span_id": f"legacy-tool-{sequence}",
                "kind": "tool",
                "name": "search_capabilities",
                "role": "retrieval",
                "status": "completed",
                "attempt": None,
                "candidate_id": None,
                "started_at": None,
                "finished_at": _safe_timestamp(event.get("created_at")),
                "duration_seconds": None,
                "start_sequence": None,
                "end_sequence": sequence,
                "schema": None,
                "error_type": None,
                "output_summary": {"result_keys": [], "returned_count": _number(data.get("count"), integer=True, minimum=0), "capability_ids": ids},
                "source_event": event_type,
                "model": None,
            })
    return spans


def _root_status(selected: list[tuple[int, dict[str, Any], str | None]], spans: list[dict[str, Any]],
                 source_status: str | None = None) -> str:
    if source_status in KNOWN_STATUSES:
        return source_status
    for _, event, event_type in reversed(selected):
        data = _data(event)
        if event_type == "RECORDED":
            intended = _safe_label(data.get("intended_status"), event=True)
            if intended in {"passed", "failed", "cancelled", "completed"}:
                return intended
        state = "cancelled" if _is_cancelled(data) else _status(event_type, data)
        if state == "cancelled":
            return "cancelled"
        if state in {"failed", "completed", "passed"} and event_type not in END_TYPES:
            return state
    if any(span["status"] == "running" for span in spans):
        return "running"
    return "running" if selected else "unknown"


def _framework(report: dict[str, Any]) -> dict[str, str | None]:
    provenance = report.get("provenance")
    runtime = provenance.get("agent_runtime") if isinstance(provenance, dict) else None
    if isinstance(runtime, dict):
        name = _safe_label(runtime.get("framework")) or _safe_label(runtime.get("name"))
        framework_version = _safe_label(runtime.get("framework_version")) or _safe_label(runtime.get("version"))
        return {"name": name, "version": framework_version}
    return {"name": None, "version": None}


def build_agent_trace(report: dict[str, Any] | None, through_sequence: int | None = None) -> dict[str, Any]:
    """Build an immutable, cursor-limited Agent replay projection."""
    source = report if isinstance(report, dict) else {}
    rows = _rows(source)
    sequences = [row[0] for row in rows]
    if through_sequence is not None:
        if isinstance(through_sequence, bool) or not isinstance(through_sequence, int) or through_sequence < 0:
            raise ValueError("through_sequence must be a nonnegative integer")
        if not sequences or through_sequence > max(sequences):
            raise ValueError("through_sequence exceeds the last legal event sequence")
    cursor = through_sequence if through_sequence is not None else (max(sequences) if sequences else None)
    selected = [row for row in rows if cursor is None or row[0] <= cursor]
    spans = _new_spans(selected)
    if not spans and not any(kind in START_TYPES or kind in END_TYPES for _, _, kind in selected):
        spans = _legacy_spans(selected)
    capability_ids: list[str] = []
    knowledge_retrievals = 0
    completed_tools = 0
    for _, event, event_type in selected:
        if event_type in {"KNOWLEDGE_RETRIEVED", "TOOL_COMPLETED"}:
            knowledge_retrievals += int(event_type == "KNOWLEDGE_RETRIEVED")
            completed_tools += int(event_type == "TOOL_COMPLETED")
            for value in _safe_ids(_data(event).get("capability_ids")):
                if value not in capability_ids:
                    capability_ids.append(value)
    return {
        "schema_version": "1.0",
        "run_id": _safe_label(source.get("run_id")),
        "status": _root_status(
            selected,
            spans,
            _safe_label(source.get("status"), event=True) if through_sequence is None else None,
        ),
        "mode": _safe_label(source.get("mode"), event=True),
        "framework": _framework(source),
        "event_count": len(selected),
        "total_event_count": len(rows),
        "cursor_sequence": cursor,
        "is_replay": through_sequence is not None,
        "spans": spans,
        "budget": _budget(source, selected, through_sequence is None and source.get("status") in {"passed", "completed", "failed", "cancelled"}),
        "evidence": {
            "capability_ids": capability_ids,
            "count": len(capability_ids),
            "retrieval_count": knowledge_retrievals or completed_tools,
        },
        "events": [_safe_event(event, event_type) for _, event, event_type in selected],
    }


__all__ = ["build_agent_trace"]
