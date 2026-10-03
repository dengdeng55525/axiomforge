"""Offline contracts for the operator-facing AxiomForge CLI diagnostics."""

import json

from pydantic import SecretStr
from typer.testing import CliRunner

from capability_factory.cli import app
from capability_factory.settings import Settings


def test_status_is_read_only_and_reports_bounded_gpu_slots(tmp_path, monkeypatch):
    settings = Settings(root=tmp_path, api_key=SecretStr("fixture-private"))
    monkeypatch.setattr("capability_factory.cli.load_settings", lambda: settings)
    monkeypatch.setattr("capability_factory.cli.probe_gpus", lambda expected_count=4: {
        "schema_version": "gpu-status.v1", "status": "partial", "expected_count": expected_count,
        "visible_count": 2, "enabled_count": 2,
        "devices": [{"index": index, "enabled": index < 2} for index in range(4)],
    })

    result = CliRunner().invoke(app, ["status", "--recent", "2"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "axiomforge-status.v1"
    assert payload["gpu_status"]["expected_count"] == 4
    assert len(payload["gpu_status"]["devices"]) == 4
    assert payload["providers"][0]["configured"] is True
    assert payload["knowledge"]["status"] == "missing"
    assert not (tmp_path / "artifacts" / "knowledge.sqlite3").exists()
    assert "fixture-private" not in result.output


def test_doctor_without_api_check_returns_safe_operator_checks(tmp_path, monkeypatch):
    settings = Settings(root=tmp_path, api_key=SecretStr("fixture-private"))
    monkeypatch.setattr("capability_factory.cli.load_settings", lambda: settings)
    monkeypatch.setattr("capability_factory.cli.probe_gpus", lambda expected_count=4: {
        "schema_version": "gpu-status.v1", "status": "unavailable", "expected_count": expected_count,
        "visible_count": 0, "enabled_count": 0, "devices": [],
    })

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "axiomforge-doctor.v1"
    assert payload["checks"]["gpu_probe_is_process_local"] is True
    assert payload["credential_configured"] is True
    assert "fixture-private" not in result.output


def test_validate_missing_database_has_nonzero_exit_and_json_reason(tmp_path, monkeypatch):
    settings = Settings(root=tmp_path)
    monkeypatch.setattr("capability_factory.cli.load_settings", lambda: settings)

    result = CliRunner().invoke(app, ["validate"])

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "axiomforge-validation.v1"
    assert payload["passed"] is False
    assert payload["knowledge"]["error"] == "database_missing"
