import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from capability_factory.api import create_app
from capability_factory.settings import Settings


def test_harness_catalog_and_run_evaluation_are_read_only(tmp_path):
    (tmp_path / "configs").mkdir()
    shutil.copy(Path("configs/agent_harness_cases.json"), tmp_path / "configs/agent_harness_cases.json")
    app = create_app(Settings(root=tmp_path))
    run_id = "e" * 32
    app.state.manager.store.save_run({
        "run_id": run_id, "status": "completed", "dataset_id": "bank",
        "selected_candidate_id": None, "candidates": [],
        "events": [
            {"sequence": 0, "event_type": "RECEIVED", "created_at": "2026-10-01T00:00:00+00:00", "data": {}},
            {"sequence": 1, "event_type": "RUN_FINISHED", "created_at": "2026-10-01T00:00:01+00:00", "data": {"status": "completed"}},
        ],
    })
    with TestClient(app) as client:
        catalog = client.get("/harness/cases")
        assert catalog.status_code == 200
        assert catalog.json()["schema_version"] == "agent-harness.v1"
        assert any(item["id"] == "trace_redaction" for item in catalog.json()["cases"])
        result = client.get(f"/runs/{run_id}/harness?case_id=trace_redaction")
        assert result.status_code == 200
        assert result.json()["schema_version"] == "agent-harness.v1"
        assert result.json()["run_id"] == run_id
        assert result.json()["passed"] is True
        suite = client.get(f"/runs/{run_id}/harness-suite")
        assert suite.status_code == 200
        assert suite.json()["schema_version"] == "agent-harness-suite.v1"
        assert suite.json()["passed"] is False
        assert "bank_e2e" in suite.json()["failed_case_ids"]
        assert client.get(f"/runs/{run_id}").json().get("harness") is None


def test_harness_unknown_case_is_404(tmp_path):
    (tmp_path / "configs").mkdir()
    shutil.copy(Path("configs/agent_harness_cases.json"), tmp_path / "configs/agent_harness_cases.json")
    app = create_app(Settings(root=tmp_path))
    run_id = "f" * 32
    app.state.manager.store.save_run({"run_id": run_id, "status": "passed", "events": []})
    with TestClient(app) as client:
        assert client.get(f"/runs/{run_id}/harness?case_id=unknown_case").status_code == 404
