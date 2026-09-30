"""Pareto analysis preserves measured costs, missingness and original selection."""

import copy

import pytest

from capability_factory.optimization import analyze_resources
from capability_factory.reporting import render_html


def candidate(identity, ap=0.8, seconds=1, rss=100, parent=None):
    return {"candidate_id": identity, "status": "passed", "parent_id": parent,
            "metrics": {"average_precision": ap},
            "resources": {"fit_seconds": seconds, "peak_rss_mib": rss}}


def test_frontier_preserves_tradeoffs_and_original_selection():
    report = {"run_id": "fixture", "selected_candidate_id": "quality",
              "candidates": [candidate("quality", 0.9, 2), candidate("fast", 0.8, 1),
                             candidate("dominated", 0.7, 3), candidate("tie", 0.8, 1)]}
    before = copy.deepcopy(report)
    analysis = analyze_resources(report)
    assert set(analysis["frontier_candidate_ids"]) == {"quality", "fast", "tie"}
    assert next(row for row in analysis["candidates"] if row["candidate_id"] == "dominated")["dominated_by"] == ["fast", "quality", "tie"]
    assert analysis["selected_candidate_id"] == "quality"
    assert report == before


@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), -1, True, "1"])
def test_missing_costs_cannot_appear_free(invalid):
    analysis = analyze_resources({"candidates": [candidate("invalid", seconds=invalid)]})
    assert analysis["frontier_candidate_ids"] == []
    assert analysis["excluded"][0]["fields"] == ["fit_seconds"]


def test_failed_candidates_and_out_of_range_ap_excluded():
    failed = candidate("failed", 1, 0, 0)
    failed["status"] = "failed"
    analysis = analyze_resources({"candidates": [failed, candidate("bad-ap", 1.5)]})
    assert len(analysis["excluded"]) == 2
    assert analysis["candidates"] == []


def test_parent_child_changes_record_improvement_without_claiming_speedup():
    report = {"candidates": [candidate("parent", 0.8, 2, 200),
                             candidate("child", 0.85, 1, 150, "parent")]}
    analysis = analyze_resources(report)
    delta = analysis["parent_child_changes"][0]
    assert delta["ap_delta"] == pytest.approx(0.05)
    assert delta["fit_seconds_delta"] == -1
    assert delta["peak_rss_mib_delta"] == -50
    assert delta["dominates_parent"] is True
    assert analysis["measurement_repetitions"] == 1


def test_html_analysis_escapes_candidate_names():
    report = {"candidates": [candidate("<script>alert(1)</script>")]}
    report["optimization"] = analyze_resources(report)
    html = render_html(report)
    assert "质量与资源权衡" in html and "峰值 RSS MiB" in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_api_derives_analysis_without_rewriting_historical_report(tmp_path):
    from fastapi.testclient import TestClient

    from capability_factory.api import create_app
    from capability_factory.settings import Settings

    application = create_app(Settings(root=tmp_path))
    report = {"run_id": "a" * 32, "status": "passed", "candidates": [candidate("historical")]}
    application.state.manager.store.save_run(report)
    with TestClient(application) as client:
        response = client.get("/runs/" + report["run_id"] + "/report")
        assert response.status_code == 200
        assert response.json()["optimization"]["frontier_candidate_ids"] == ["historical"]
        assert "optimization" not in application.state.manager.store.get_run(report["run_id"])
