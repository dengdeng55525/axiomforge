"""Offline Agent harness contract and redaction tests."""

from pathlib import Path

import pytest

from capability_factory.harness import evaluate_report, evaluate_suite, load_cases


def _report(status="passed", dataset_id="bank"):
    events = []

    def add(kind, **data):
        events.append({"sequence": len(events), "event_type": kind,
                       "created_at": f"2026-10-01T00:00:{len(events):02d}+00:00", "data": data})

    add("RECEIVED", role="system")
    add("AGENT_STARTED", span_id="a-interpreter", name="interpreter", role="interpreter")
    add("AGENT_COMPLETED", span_id="a-interpreter", name="interpreter", role="interpreter", result_keys=["objective"])
    add("AGENT_STARTED", span_id="a-planner", name="planner", role="planner")
    add("AGENT_COMPLETED", span_id="a-planner", name="planner", role="planner", result_keys=["candidates"])
    add("AGENT_STARTED", span_id="a-coder", name="coder", role="coder")
    add("AGENT_COMPLETED", span_id="a-coder", name="coder", role="coder", result_keys=["code"])
    add("SPEC_VALIDATED")
    add("KNOWLEDGE_RETRIEVED", capability_ids=["cap-bank"])
    add("CANDIDATE_PLANNED", candidate_id="c1")
    add("VALIDATING", candidate_id="c1")
    add("VERIFIED", candidate_id="c1", status="passed")
    add("COMPARED", selected_candidate_id="c1")
    add("RECORDED", intended_status=status)
    add("RUN_FINISHED", status=status)
    return {
        "schema_version": "1.0", "run_id": "a" * 32, "status": status,
        "dataset_id": dataset_id, "selected_candidate_id": "c1",
        "candidates": [{"candidate_id": "c1", "status": status,
                        "metrics": {"average_precision": 0.81},
                        "repairs": [], "attempts": [{"attempt": 0}]}],
        "events": events, "timing": {"wall_seconds": 1.5},
        "provenance": {"agent_runtime": {"framework": "langchain-core", "version": "1.6.6"}},
    }


def test_bank_case_scores_and_preserves_trace_contract():
    case = next(item for item in load_cases(Path("configs/agent_harness_cases.json")) if item.id == "bank_e2e")
    result = evaluate_report(_report(), case)
    assert result.passed is True
    assert result.score == 1.0
    assert result.summary["hard_passed"] == result.summary["hard_checks"]
    assert result.trace["evidence"]["capability_ids"] == ["cap-bank"]


def test_dataset_or_event_gap_fails_with_explicit_evidence():
    case = next(item for item in load_cases(Path("configs/agent_harness_cases.json")) if item.id == "bank_e2e")
    report = _report(dataset_id="sms")
    report["events"] = [event for event in report["events"] if event["event_type"] != "COMPARED"]
    result = evaluate_report(report, case)
    assert result.passed is False
    assert any(item.id == "dataset_contract" and not item.passed for item in result.checks)
    workflow = next(item for item in result.checks if item.id == "workflow_events")
    assert "COMPARED" in workflow.expected
    assert "COMPARED" not in workflow.observed


def test_forbidden_event_payload_is_rejected_and_case_file_has_unique_ids():
    cases = load_cases(Path("configs/agent_harness_cases.json"))
    assert len({item.id for item in cases}) == len(cases)
    case = next(item for item in cases if item.id == "trace_redaction")
    report = _report()
    report["events"][0]["data"]["prompt"] = "secret prompt should never be in event facts"
    result = evaluate_report(report, case)
    redaction = next(item for item in result.checks if item.id == "trace_redaction")
    assert redaction.passed is False
    assert redaction.observed == ["events[0].data.prompt"]


def test_case_loader_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text('{"cases":[{"id":"same","title":"a"},{"id":"same","title":"b"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        load_cases(path)


def test_suite_aggregates_case_results_without_mutating_report():
    cases = load_cases(Path("configs/agent_harness_cases.json"))
    report = _report()
    suite = evaluate_suite(report, [next(item for item in cases if item.id == "trace_redaction")])
    assert suite["schema_version"] == "agent-harness-suite.v1"
    assert suite["case_count"] == 1
    assert suite["passed_cases"] == 1
    assert suite["failed_case_ids"] == []
