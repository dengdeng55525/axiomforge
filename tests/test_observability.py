"""Pure Agent trace projections: replay safety, span contracts and redaction."""

from __future__ import annotations

import copy

import pytest

from capability_factory.observability import build_agent_trace


def event(sequence, event_type, created_at, **data):
    return {
        "sequence": sequence,
        "event_type": event_type,
        "created_at": created_at,
        "data": data,
    }


def report_with_events(events, **overrides):
    value = {
        "run_id": "run-observability",
        "status": "passed",
        "mode": "real",
        "provenance": {"agent_runtime": {"framework": "langchain-core", "version": "1.6.6"}},
        "request": {
            "max_seconds": 900,
            "max_candidates": 2,
        },
        "resource_budget": {
            "max_calls": 24,
            "max_input_tokens": 200000,
            "max_output_tokens": 40000,
        },
        "usage": {
            "calls": 4,
            "input_tokens": 9999,
            "output_tokens": 999,
            "cached_input_tokens": 9,
        },
        "timing": {"wall_seconds": 12.5},
        "events": events,
    }
    value.update(overrides)
    return value


def test_successful_agent_tool_trace_has_replayable_spans_and_safe_summaries():
    report = report_with_events([
        event(0, "AGENT_STARTED", "2026-09-30T00:00:00+00:00", span_id="agent-interpreter",
              name="interpreter", role="interpreter", attempt=0, schema="TaskInterpretation",
              model="gpt-5.5"),
        event(1, "TOOL_STARTED", "2026-09-30T00:00:01+00:00", span_id="tool-search",
              name="search_capabilities", role="retrieval", schema="CapabilitySearch"),
        event(2, "TOOL_COMPLETED", "2026-09-30T00:00:02+00:00", span_id="tool-search",
              name="search_capabilities", role="retrieval", duration_seconds=1.0,
              returned_count=3, capability_ids=["cap-bank", "cap-logistic"]),
        event(3, "AGENT_COMPLETED", "2026-09-30T00:00:04+00:00", span_id="agent-interpreter",
              name="interpreter", role="interpreter", duration_seconds=4.0,
              result_keys=["objective", "constraints"], returned_count=1),
        event(4, "LLM_RESPONSE", "2026-09-30T00:00:05+00:00", role="interpreter",
              input_tokens=100, output_tokens=20, cached_input_tokens=3),
        event(5, "RECORDED", "2026-09-30T00:00:06+00:00", intended_status="passed"),
    ])
    original = copy.deepcopy(report)
    trace = build_agent_trace(report)

    assert trace["schema_version"] == "1.0"
    assert trace["run_id"] == "run-observability"
    assert trace["status"] == "passed"
    assert trace["framework"] == {"name": "langchain-core", "version": "1.6.6"}
    assert trace["event_count"] == trace["total_event_count"] == 6
    assert trace["cursor_sequence"] == 5
    assert trace["is_replay"] is False
    assert [span["span_id"] for span in trace["spans"]] == ["agent-interpreter", "tool-search"]
    agent, tool = trace["spans"]
    assert agent["kind"] == "agent" and agent["status"] == "completed"
    assert agent["start_sequence"] == 0 and agent["end_sequence"] == 3
    assert agent["duration_seconds"] == 4.0
    assert agent["output_summary"] == {
        "result_keys": ["objective", "constraints"], "returned_count": 1, "capability_ids": [],
    }
    assert tool["kind"] == "tool" and tool["status"] == "completed"
    assert tool["duration_seconds"] == 1.0
    assert tool["output_summary"]["capability_ids"] == ["cap-bank", "cap-logistic"]
    assert trace["evidence"] == {
        "capability_ids": ["cap-bank", "cap-logistic"], "count": 2, "retrieval_count": 1,
    }
    assert trace["budget"]["calls"] == 4
    assert trace["budget"]["input_tokens"] == 100
    assert trace["budget"]["output_tokens"] == 20
    assert trace["budget"]["cached_input_tokens"] == 3
    assert trace["budget"]["max_calls"] == 24
    assert trace["budget"]["max_input_tokens"] == 200000
    assert trace["budget"]["max_output_tokens"] == 40000
    assert trace["budget"]["max_seconds"] == 900
    assert trace["budget"]["wall_seconds"] == 12.5
    assert trace["events"][1] == {
        "sequence": 1, "event_type": "TOOL_STARTED",
        "created_at": "2026-09-30T00:00:01+00:00", "role": "retrieval",
        "span_id": "tool-search", "name": "search_capabilities", "status": "running",
    }
    assert report == original


def test_rejected_failed_and_cancelled_spans_keep_terminal_state():
    report = report_with_events([
        event(0, "AGENT_STARTED", "2026-09-30T00:00:00Z", span_id="a-reject",
              name="coder", role="coder", attempt=0, candidate_id="c1"),
        event(1, "AGENT_REJECTED", "2026-09-30T00:00:01Z", span_id="a-reject",
              error_type="ResponseContractError", result_keys=["error_type"]),
        event(2, "AGENT_STARTED", "2026-09-30T00:00:02Z", span_id="a-fail",
              name="reviewer", role="reviewer", candidate_id="c1"),
        event(3, "AGENT_FAILED", "2026-09-30T00:00:03Z", span_id="a-fail",
              error_type="RuntimeError", status="failed"),
        event(4, "AGENT_STARTED", "2026-09-30T00:00:04Z", span_id="a-cancel",
              name="repair_coder", role="repair_coder"),
        event(5, "AGENT_FAILED", "2026-09-30T00:00:05Z", span_id="a-cancel",
              error_type="Cancelled"),
    ], status=None)
    report.pop("status", None)
    trace = build_agent_trace(report)
    by_id = {span["span_id"]: span for span in trace["spans"]}
    assert by_id["a-reject"]["status"] == "rejected"
    assert by_id["a-reject"]["error_type"] == "ResponseContractError"
    assert by_id["a-fail"]["status"] == "failed"
    assert by_id["a-fail"]["error_type"] == "RuntimeError"
    assert by_id["a-cancel"]["status"] == "cancelled"
    assert trace["status"] == "cancelled"
    assert all(span["duration_seconds"] is None for span in by_id.values())


def test_in_progress_span_has_no_invented_duration_or_finish():
    report = report_with_events([
        event(0, "AGENT_STARTED", "2026-09-30T00:00:00+00:00", span_id="agent-running",
              name="planner", role="planner", attempt=1),
        event(1, "TOOL_STARTED", "2026-09-30T00:00:03+00:00", span_id="tool-running",
              name="search_capabilities", role="retrieval"),
    ], status="running")
    trace = build_agent_trace(report)
    assert trace["status"] == "running"
    assert all(span["status"] == "running" for span in trace["spans"])
    assert all(span["finished_at"] is None and span["duration_seconds"] is None for span in trace["spans"])


def test_legacy_events_become_completed_summary_spans_without_fake_starts():
    report = report_with_events([
        event(0, "LLM_RESPONSE", "2026-09-30T00:00:00+00:00", role="planner",
              returned_model="coder14", seconds=2.4, input_tokens=7, output_tokens=3,
              cached_input_tokens=0),
        event(1, "KNOWLEDGE_RETRIEVED", "2026-09-30T00:00:01+00:00",
              capability_ids=["cap-one", "cap-two"], count=2),
        event(2, "MOCK_RESPONSE", "2026-09-30T00:00:02+00:00", role="coder", seconds=0.1),
    ])
    trace = build_agent_trace(report)
    assert all(span["source_event"] in {"LLM_RESPONSE", "MOCK_RESPONSE", "KNOWLEDGE_RETRIEVED"}
               for span in trace["spans"])
    assert trace["spans"][0]["start_sequence"] is None
    assert trace["spans"][0]["finished_at"] == "2026-09-30T00:00:00+00:00"
    retrieval = next(span for span in trace["spans"] if span["kind"] == "tool")
    assert retrieval["output_summary"]["capability_ids"] == ["cap-one", "cap-two"]
    assert trace["evidence"]["retrieval_count"] == 1
    assert trace["budget"]["calls"] == 4
    assert trace["budget"]["input_tokens"] == 7
    assert trace["budget"]["output_tokens"] == 3


def test_replay_cursor_excludes_future_tokens_evidence_spans_and_report_values():
    report = report_with_events([
        event(0, "LLM_RESPONSE", "2026-09-30T00:00:00Z", role="interpreter",
              input_tokens=10, output_tokens=4, cached_input_tokens=1),
        event(1, "KNOWLEDGE_RETRIEVED", "2026-09-30T00:00:01Z", capability_ids=["cap-visible"]),
        event(2, "AGENT_STARTED", "2026-09-30T00:00:02Z", span_id="future-agent",
              name="coder", role="coder"),
        event(3, "LLM_RESPONSE", "2026-09-30T00:00:03Z", role="coder",
              input_tokens=900, output_tokens=800, cached_input_tokens=50),
        event(4, "TOOL_COMPLETED", "2026-09-30T00:00:04Z", span_id="future-tool",
              name="search_capabilities", capability_ids=["cap-future"]),
        event(5, "RECORDED", "2026-09-30T00:00:05Z", intended_status="passed"),
    ])
    trace = build_agent_trace(report, through_sequence=1)
    assert trace["is_replay"] is True and trace["cursor_sequence"] == 1
    assert trace["event_count"] == 2 and trace["total_event_count"] == 6
    assert trace["budget"]["calls"] == 1
    assert trace["budget"]["input_tokens"] == 10
    assert trace["budget"]["output_tokens"] == 4
    assert trace["budget"]["cached_input_tokens"] == 1
    assert trace["evidence"]["capability_ids"] == ["cap-visible"]
    assert "cap-future" not in str(trace)
    assert "future-agent" not in str(trace)
    assert trace["status"] == "running"


def test_cursor_uses_budget_event_and_event_timestamps_only():
    report = report_with_events([
        event(0, "RUN_BUDGET_APPLIED", "2026-09-30T00:00:00Z", effective_seconds=120),
        event(1, "AGENT_STARTED", "2026-09-30T00:00:05Z", span_id="a",
              name="planner", role="planner"),
        event(2, "LLM_RESPONSE", "2026-09-30T00:00:07Z", role="planner",
              input_tokens=1, output_tokens=2, cached_input_tokens=0),
    ])
    trace = build_agent_trace(report, through_sequence=2)
    assert trace["budget"]["max_seconds"] == 120
    assert trace["budget"]["wall_seconds"] == 7


def test_full_report_terminal_status_takes_precedence_over_earlier_recorded_intent():
    report = report_with_events([
        event(0, "RECORDED", "2026-09-30T00:00:00Z", intended_status="passed"),
        event(1, "RUN_FINISHED", "2026-09-30T00:00:01Z", status="failed"),
    ], status="failed")
    trace = build_agent_trace(report)
    assert trace["status"] == "failed"
    replay = build_agent_trace(report, through_sequence=0)
    assert replay["status"] == "passed"


def test_full_usage_calls_can_include_transport_retries_but_replay_cannot():
    report = report_with_events([
        event(0, "LLM_RESPONSE", "2026-09-30T00:00:00Z", input_tokens=4, output_tokens=2,
              cached_input_tokens=0),
    ], usage={"calls": 3, "input_tokens": 4, "output_tokens": 2, "cached_input_tokens": 0})
    full = build_agent_trace(report)
    replay = build_agent_trace(report, through_sequence=0)
    assert full["budget"]["calls"] == 3
    assert replay["budget"]["calls"] == 1


def test_malformed_and_untrusted_events_are_conservative_and_nonmutating():
    report = report_with_events([
        {"sequence": -1, "event_type": "NEGATIVE", "data": {"prompt": "drop"}},
        {"sequence": True, "event_type": "BOOL", "data": {"code": "drop"}},
        event(0, "<script>alert(1)</script>", "bad timestamp", span_id="<span>",
              name="</pre><script>", role="planner", prompt="PRIVATE_PROMPT", code="PRIVATE_CODE"),
        event(2, "TOOL_COMPLETED", "2026-09-30T00:00:02Z", span_id="tool", capability_ids=["safe"]),
        {"sequence": "3", "event_type": "STRING_SEQ", "created_at": "2026-09-30T00:00:03Z"},
    ])
    original = copy.deepcopy(report)
    trace = build_agent_trace(report)
    assert trace["total_event_count"] == trace["event_count"] == 2
    assert trace["events"][0]["event_type"] == "unknown"
    assert "script" not in str(trace).lower()
    assert "private_prompt" not in str(trace).lower()
    assert "private_code" not in str(trace).lower()
    assert trace["events"][0]["created_at"] is None
    assert report == original


def test_empty_and_legacy_missing_limits_do_not_invent_metrics_or_budgets():
    trace = build_agent_trace({})
    assert trace["event_count"] == 0
    assert trace["total_event_count"] == 0
    assert trace["spans"] == []
    assert trace["status"] == "unknown"
    assert trace["budget"]["calls"] == 0
    assert trace["budget"]["input_tokens"] is None
    assert trace["budget"]["max_calls"] is None
    assert trace["budget"]["max_seconds"] is None
    trace = build_agent_trace({"run_id": "legacy", "status": "failed", "events": []})
    assert trace["status"] == "failed"


@pytest.mark.parametrize("cursor", [-1, True, 1.2, "1", 10])
def test_invalid_cursor_is_rejected(cursor):
    report = report_with_events([event(0, "LLM_RESPONSE", "2026-09-30T00:00:00Z")])
    with pytest.raises(ValueError):
        build_agent_trace(report, through_sequence=cursor)


def test_output_summaries_never_copy_untrusted_full_values():
    report = report_with_events([
        event(0, "AGENT_STARTED", "2026-09-30T00:00:00Z", span_id="safe", name="coder"),
        event(1, "AGENT_COMPLETED", "2026-09-30T00:00:01Z", span_id="safe",
              result_keys=["safe"], returned_count=1, capability_ids=["safe"],
              prompt="PRIVATE_PROMPT", code="PRIVATE_CODE", reasoning="PRIVATE_REASONING"),
    ])
    trace = build_agent_trace(report)
    serialized = str(trace)
    assert "PRIVATE_PROMPT" not in serialized
    assert "PRIVATE_CODE" not in serialized
    assert "PRIVATE_REASONING" not in serialized
    assert trace["spans"][0]["output_summary"] == {
        "result_keys": ["safe"], "returned_count": 1, "capability_ids": ["safe"],
    }
