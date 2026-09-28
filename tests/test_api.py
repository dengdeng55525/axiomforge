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
