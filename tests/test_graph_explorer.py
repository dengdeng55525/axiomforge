"""Graph UI contracts preserve provenance, filters, bounds and validation facts."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from capability_factory.api import create_app
from capability_factory.graph_presentation import summarize_checks
from capability_factory.settings import Settings


@pytest.fixture
def graph_app(tmp_path):
    app = create_app(Settings(root=tmp_path))
    store = app.state.manager.store
    source = {
        "source_id": "src:fixture", "source_key": "public-code-fixture", "uri": "repo://example/model.py",
        "revision": "fixture-revision", "content_sha256": "a" * 64, "locator": {"start_line": 1, "end_line": 9},
        "license": "MIT", "content": "full code should not be returned in the explorer",
    }
    card = store._validate_card({
        "capability_id": "fixture-logistic", "name": "Logistic capability", "summary": "Source-grounded fixture",
        "task_types": ["tabular_binary_classification"], "evidence": [source["source_id"]],
        "origin": "manual_seed", "status": "extracted", "dependencies": ["scikit-learn"],
        "uses": [{"kind": "Algorithm", "label": "LogisticRegression"},
                 {"kind": "Transform", "label": "StandardScaler"}],
    }, {source["source_id"]: source})
    with store._connection(write=True) as connection:
        store._source(connection, source)
        store._put_card(connection, card)
        store._put_card(connection, {**card, "summary": "Second immutable capability version"})
        store._node(connection, "source:extra-code", "Source", "Code fixture", {
            "uri": "repo://example/extra.py", "content": "DO_NOT_EXPOSE_CONTENT", "code": "DO_NOT_EXPOSE_CODE",
            "source_code": "DO_NOT_EXPOSE_SOURCE", "license": "MIT",
        })
    run_id = "a" * 32
    store.save_run({
        "run_id": run_id, "status": "passed", "mode": "mock", "provider": "mock", "dataset_id": "bank",
        "task_spec": {"primary_metric": "average_precision"}, "selected_candidate_id": "candidate-1",
        "candidates": [{
            "candidate_id": "candidate-1", "status": "passed", "quality_status": "baseline_or_worse",
            "plan": {"algorithm": "logistic", "evidence_ids": ["fixture-logistic"]},
            "metrics": {"average_precision": 0.1},
            "checks": [{"name": "prediction_contract", "mandatory": True, "passed": True},
                       {"name": "ap_above_dummy", "mandatory": False, "passed": False}],
            "attempts": [{"attempt": 0, "code_sha256": "b" * 64, "code_path": "candidate.py",
                          "status": "passed", "metrics": {"average_precision": 0.1}}],
        }],
    })
    # Sharing a dataset must not turn this unrelated run into capability evidence.
    store.save_run({"run_id": "b" * 32, "status": "passed", "mode": "real", "dataset_id": "bank"})
    return app


def test_empty_explorer_and_legacy_graph_are_well_formed(tmp_path):
    with TestClient(create_app(Settings(root=tmp_path))) as client:
        payload = client.get("/graph/explore").json()
        assert payload["nodes"] == payload["edges"] == []
        assert payload["stats"]["total_nodes"] == payload["stats"]["total_edges"] == 0
        assert payload["truncated"] is False
        assert payload["focus"] is payload["evidence"] is None
        assert payload["facets"] == {"kinds": [], "relations": []}
        assert client.get("/graph").json() == {"nodes": [], "edges": []}


def test_focus_supports_colons_and_exact_provenance_paths(graph_app):
    with TestClient(graph_app) as client:
        response = client.get("/graph/explore", params={"focus": "capability:fixture-logistic:v2", "hops": 2})
        assert response.status_code == 200
        payload = response.json()
        assert payload["nodes"][0]["id"] == "capability:fixture-logistic:v2"
        assert payload["focus"]["distance"] == 0
        evidence = payload["evidence"]
        source = next(item for item in evidence["sources"] if item["node_id"] == "src:fixture")
        assert source["properties"]["content_sha256"] == "a" * 64
        assert source["properties"]["locator"] == {"start_line": 1, "end_line": 9}
        assert source["path"][0]["relation"] == "DERIVED_FROM"
        assert [item["run_id"] for item in evidence["validations"]] == ["a" * 32]
        validation = evidence["validations"][0]
        assert [edge["relation"] for edge in validation["path"]] == ["IMPLEMENTS", "EVALUATES"]
        assert validation["mode"] == "mock"
        assert validation["metrics"] == {"average_precision": 0.1}
        assert validation["quality_status"] == "baseline_or_worse"
        assert validation["checks"]["mandatory_failed"] == 0
        assert validation["checks"]["failed"] == 1
        assert payload["focus"]["properties"]["status"] == "extracted"


def test_comma_filters_global_legends_and_focus_retention(graph_app):
    with TestClient(graph_app) as client:
        overview = client.get("/graph/explore").json()
        payload = client.get("/graph/explore", params={
            "focus": "capability:fixture-logistic:v2", "hops": 1,
            "kinds": "Algorithm, Transform", "relations": "USES,REQUIRES", "q": "LOGISTICREGRESSION",
        }).json()
        assert {node["id"] for node in payload["nodes"]} == {
            "capability:fixture-logistic:v2", "algorithm:LogisticRegression",
        }
        assert payload["filters"]["focus_retained_outside_filters"] is True
        assert payload["filters"]["kinds"] == ["Algorithm", "Transform"]
        assert payload["facets"] == overview["facets"]
        assert payload["stats"]["hidden_by_filters"] > 0
        assert payload["edges"][0]["relation_label"] == "使用"


def test_limits_report_every_omission_and_never_dangle_edges(graph_app):
    with TestClient(graph_app) as client:
        params = {"focus": "capability:fixture-logistic:v2", "hops": 2, "limit": 2, "edge_limit": 1}
        payload = client.get("/graph/explore", params=params).json()
        assert payload == client.get("/graph/explore", params=params).json()
        assert len(payload["nodes"]) == 2
        assert len(payload["edges"]) <= 1
        stats = payload["stats"]
        assert stats["omitted_nodes"] == stats["matched_nodes"] - stats["returned_nodes"] > 0
        assert stats["omitted_edges"] == stats["matched_edges"] - stats["returned_edges"] > 0
        assert payload["truncated"] is True
        identities = {node["id"] for node in payload["nodes"]}
        assert all(edge["source"] in identities and edge["target"] in identities for edge in payload["edges"])
        zero_edges = client.get("/graph/explore", params={"edge_limit": 0}).json()
        assert zero_edges["edges"] == []
        assert zero_edges["stats"]["omitted_edges"] == zero_edges["stats"]["matched_edges"] > 0


@pytest.mark.parametrize("params", [
    {"hops": 0}, {"hops": 3}, {"limit": 0}, {"limit": 501},
    {"edge_limit": -1}, {"edge_limit": 1501}, {"q": "x" * 201}, {"focus": "x" * 513},
])
def test_explorer_rejects_unbounded_parameters(tmp_path, params):
    with TestClient(create_app(Settings(root=tmp_path))) as client:
        assert client.get("/graph/explore", params=params).status_code == 422


def test_unknown_focus_and_filters_have_explicit_behavior(graph_app):
    with TestClient(graph_app) as client:
        assert client.get("/graph/explore", params={"focus": "capability:missing:v1"}).status_code == 404
        empty = client.get("/graph/explore", params={"kinds": "UnknownType"}).json()
        assert empty["nodes"] == []
        assert empty["truncated"] is False
        assert empty["stats"]["hidden_by_filters"] == empty["stats"]["total_nodes"]


def test_capability_details_preserve_versions_and_evidence(graph_app):
    with TestClient(graph_app) as client:
        latest = client.get("/capabilities/fixture-logistic").json()
        assert latest["latest_version"] == latest["capability"]["version"] == 2
        assert latest["version_count"] == 2
        assert [item["version"] for item in latest["versions"]] == [2, 1]
        assert all(len(item["content_sha256"]) == 64 for item in latest["versions"])
        assert latest["evidence"]["validations"][0]["run_id"] == "a" * 32
        old = client.get("/capabilities/fixture-logistic", params={"version": 1}).json()
        assert old["capability"]["summary"] == "Source-grounded fixture"
        assert old["capability"]["version"] == 1
        assert old["evidence"]["validations"] == []
        assert client.get("/capabilities/fixture-logistic", params={"version": 99}).status_code == 404
        assert client.get("/capabilities/unknown").status_code == 404
        assert client.get("/capabilities/fixture-logistic", params={"version": 0}).status_code == 422


def test_explorer_omits_source_code_and_preserves_raw_endpoint(graph_app):
    with TestClient(graph_app) as client:
        overview = client.get("/graph/explore")
        focus = client.get("/graph/explore", params={"focus": "source:extra-code"})
        assert "DO_NOT_EXPOSE" not in overview.text
        assert "DO_NOT_EXPOSE" not in focus.text
        assert "DO_NOT_EXPOSE" in client.get("/graph").text


def test_summary_translates_quality_and_real_check_lists_without_changing_report(graph_app):
    with TestClient(graph_app) as client:
        run_id = "a" * 32
        summary = client.get(f"/runs/{run_id}/summary").json()
        assert summary["quality_status"] == "baseline_or_worse"
        assert "未超过" in summary["quality_label"]
        validation = summary["validation"]
        assert validation["checks"]["total"] == 2
        assert validation["checks"]["all_mandatory_passed"] is True
        assert validation["checks"]["failed"] == 1
        metrics = client.get(f"/runs/{run_id}/metrics").json()
        assert len(metrics["candidates"][0]["checks"]) == 2
        assert "quality_status" not in client.get(f"/runs/{run_id}/report").json()


def test_missing_checks_are_unknown_not_passed():
    assert summarize_checks(None)["all_mandatory_passed"] is None
    checks = summarize_checks([{"name": "unset", "mandatory": True}, None, "legacy"])
    assert checks["total"] == checks["unknown"] == 1
    assert checks["all_mandatory_passed"] is False
