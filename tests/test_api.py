"""API rejects unsafe inputs and returns durable terminal errors."""

import time

from fastapi.testclient import TestClient

from capability_factory.api import create_app
from capability_factory.settings import Settings


def test_health_and_invalid_request_do_not_expose_configuration(tmp_path):
    app = create_app(Settings(root=tmp_path))
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["local_model_deployed"] is False
        assert "api_key" not in health.text
        assert client.post("/runs", json={"description": "unsafe path request", "dataset_id": "../../secret"}).status_code == 422
        assert client.post("/runs", json={"description": "invalid budget", "max_candidates": 999}).status_code == 422
        assert client.get("/runs/not-a-run").status_code == 404


def test_unhandled_future_failure_is_reconciled(monkeypatch, tmp_path):
    def crash(*args, **kwargs):
        raise RuntimeError("fixture setup failure")

    monkeypatch.setattr("capability_factory.api.Workflow.run", crash)
    app = create_app(Settings(root=tmp_path))
    with TestClient(app) as client:
        created = client.post("/runs", json={"description": "exercise unhandled initialization failure", "provider": "mock"})
        run_id = created.json()["run_id"]
        for _ in range(100):
            report = client.get(f"/runs/{run_id}").json()
            if report["status"] == "failed":
                break
            time.sleep(0.01)
        assert report["status"] == "failed"
        assert "Unhandled RuntimeError" in report["failure_reason"]


def test_artifact_path_cannot_escape_run_directory(tmp_path):
    app = create_app(Settings(root=tmp_path))
    run_id = "a" * 32
    app.state.manager.store.save_run({"run_id": run_id, "status": "passed", "candidates": [
        {"candidate_id": "c1", "artifact_id": "c1", "status": "passed", "code_path": "../../../../secret.py"}]})
    with TestClient(app) as client:
        assert client.get(f"/runs/{run_id}/artifacts/c1").status_code == 404
        assert client.get("/graph").status_code == 200
        assert client.get("/capabilities").status_code == 200


def test_visual_configuration_has_api_and_future_local_14b_without_secrets(tmp_path):
    settings = Settings(
        root=tmp_path,
        api_key="fixture-secret-should-never-be-serialized",
        base_url="https://api.deepseek.com/v1?token=should-not-appear",
        local_base_url="http://user:password@127.0.0.1:8100/v1?key=hidden",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        providers = client.get("/config/providers")
        assert providers.status_code == 200
        payload = providers.json()
        assert payload["default_provider"] == "deepseek"
        by_id = {item["id"]: item for item in payload["providers"]}
        assert by_id["deepseek"]["available"] is True
        assert by_id["deepseek"]["endpoint"] == "https://api.deepseek.com/v1"
        assert by_id["local_http"]["status"] == "planned_not_deployed"
        assert by_id["local_http"]["available"] is False
        assert by_id["local_http"]["model_plan"]["gpu_count"] == 4
        assert by_id["local_http"]["model_plan"]["model_family"].endswith("14B-Instruct-AWQ")
        assert "fixture-secret" not in providers.text
        assert "password" not in providers.text
        health = client.get("/health")
        assert health.status_code == 200
        assert "password" not in health.text
        assert health.json()["local_provider"]["base_url"] is None
        profiles = client.get("/inference/profiles")
        assert profiles.status_code == 200
        assert "password" not in profiles.text
        assert profiles.json()["active_local"]["base_url"] is None
        config = client.get("/config").json()
        assert {item["id"] for item in config["datasets"]} == {"bank", "sms"}
        assert client.get("/config/datasets").json()["datasets"]


def test_visual_run_metrics_resources_and_timeline_are_compact(tmp_path):
    app = create_app(Settings(root=tmp_path))
    run_id = "b" * 32
    app.state.manager.store.save_run({
        "run_id": run_id,
        "status": "passed",
        "provider": "mock",
        "mode": "mock",
        "model": "deterministic-mock-v1",
        "dataset_id": "bank",
        "task_spec": {"primary_metric": "average_precision"},
        "selected_candidate_id": "bank_lr",
        "quality_status": "above_prevalence",
        "candidates": [{
            "candidate_id": "bank_lr",
            "plan": {"algorithm": "logistic", "variant": "default"},
            "status": "passed",
            "quality_status": "above_prevalence",
            "metrics": {"average_precision": 0.3, "roc_auc": 0.7},
            "resources": {"wall_seconds": 1.2, "fit_seconds": 0.3,
                          "peak_rss_mib": 123.0, "limits": {"memory_mib": 2048}},
        }],
        "usage": {"calls": 2, "input_tokens": 10, "output_tokens": 20},
        "timing": {"wall_seconds": 3.4},
        "events": [{"sequence": 0, "event_type": "RECEIVED", "created_at": "now",
                    "data": {"role": "interpreter"}}],
    })
    with TestClient(app) as client:
        metrics = client.get(f"/runs/{run_id}/metrics")
        assert metrics.status_code == 200
        assert metrics.json()["best_observed_candidate_id"] == "bank_lr"
        assert metrics.json()["candidates"][0]["metrics"]["average_precision"] == 0.3
        resources = client.get(f"/runs/{run_id}/resources").json()
        assert resources["peak_candidate_rss_mib"] == 123.0
        assert resources["usage"]["calls"] == 2
        timeline = client.get(f"/runs/{run_id}/timeline").json()
        assert timeline["event_count"] == 1
        assert timeline["events"][0]["role"] == "interpreter"
        summary = client.get(f"/runs/{run_id}/summary").json()
        assert summary["metrics"]["selected_candidate_id"] == "bank_lr"
        assert summary["resources"]["run_id"] == run_id
        markdown = client.get(f"/runs/{run_id}/report.md")
        assert markdown.status_code == 200
        assert "算法能力验证报告" in markdown.text
