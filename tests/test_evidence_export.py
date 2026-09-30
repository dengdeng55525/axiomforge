"""Portable exports preserve observations without copying private run inputs."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_evidence.py"
SPEC = importlib.util.spec_from_file_location("evidence_export_test_module", SCRIPT)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)
RUN_ID = "a" * 32


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


@pytest.fixture
def fixture(tmp_path):
    project = tmp_path / "project"
    directory = project / "artifacts" / "runs" / RUN_ID
    report = {
        "run_id": RUN_ID, "status": "passed", "mode": "real", "provider": "deepseek",
        "model": "test-fixture-model", "description": "public fixture",
        "candidates": [], "selected_candidate_id": "c1",
        "usage": {"calls": 4, "records": [{"prompt_sha256": "b" * 64, "response_sha256": "c" * 64}]},
        "provenance": {"path": str(directory / "dataset" / "train.json")},
        "warnings": ["source " + str(project / "knowledge" / "notes.md")],
    }
    for candidate_id, statuses in [("c1", ["failed", "passed"]), ("c2", ["failed"])]:
        candidate = {"candidate_id": candidate_id, "status": statuses[-1], "attempts": [],
                     "metrics": {"average_precision": 0.3} if statuses[-1] == "passed" else {}}
        for attempt, status in enumerate(statuses):
            relative = Path("candidates") / candidate_id / f"attempt_{attempt}" / "model.py"
            code = f"# {candidate_id} attempt {attempt}\ndef build_pipeline(task_spec):\n    return None\n"
            digest = hashlib.sha256(code.encode()).hexdigest()
            code_path = directory / relative
            code_path.parent.mkdir(parents=True, exist_ok=True)
            code_path.write_text(code)
            verification = {"status": status, "source_sha256": digest, "metrics": candidate["metrics"],
                            "artifact_paths": {"source": str(code_path),
                                               "predictions": str(code_path.parent / "predictions.json")}}
            write_json(code_path.parent / "verification.json", verification)
            write_json(code_path.parent / "predictions.json", {"private": "not exported"})
            write_json(code_path.parent / "model_metadata.json", {"actual_algorithm": "fixture"})
            snapshot = {"attempt": attempt, "status": status, "code_path": relative.as_posix(),
                        "code_sha256": digest, "metrics": candidate["metrics"]}
            candidate["attempts"].append(snapshot)
        candidate.update(code_path=snapshot["code_path"], code_sha256=snapshot["code_sha256"])
        report["candidates"].append(candidate)
    write_json(directory / "report.json", report)
    write_json(directory / "dataset" / "train.json", {"private_training_data": True})
    write_json(directory / "llm" / "01.request.json", {"private_prompt": True})
    (project / ".env").write_text("must never read or export this fixture")
    return project, directory, report


def test_export_preserves_failed_attempts_usage_mode_and_hashes(fixture):
    project, directory, original = fixture
    original_bytes = (directory / "report.json").read_bytes()
    result = exporter.export_run(project, RUN_ID, "bank_demo", "Historical pre-fix fixture.")
    destination = project / result["directory"]
    public = json.loads((destination / "report.json").read_text())
    manifest = json.loads((destination / "manifest.json").read_text())
    assert public["mode"] == original["mode"] == "real"
    assert public["usage"] == original["usage"]
    assert public["candidates"] == original["candidates"]
    assert manifest["attempt_count"] == 3
    assert manifest["source_report_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert "Historical pre-fix fixture." in public["evidence_export"]["note"]
    assert "Historical pre-fix fixture." in (destination / "report.html").read_text()
    assert public["provenance"]["path"] == f"artifacts/runs/{RUN_ID}/dataset/train.json"
    for entry in manifest["files"]:
        path = destination / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        assert str(project) not in path.read_text()
    assert (destination / "candidates/c1/attempt_0/model.py").exists()
    assert json.loads((destination / "candidates/c1/attempt_0/verification.json").read_text())["status"] == "failed"
    assert json.loads((destination / "candidates/c2/verification.json").read_text())["status"] == "failed"
    names = {path.name for path in destination.rglob("*") if path.is_file()}
    assert names == {"model.py", "verification.json", "metadata.json", "report.json", "report.html", "report.md", "manifest.json"}
    assert (directory / "report.json").read_bytes() == original_bytes
    assert (project / ".env").read_text() == "must never read or export this fixture"


@pytest.mark.parametrize("run_id,name", [("../outside", "demo"), (RUN_ID, "../outside"), (RUN_ID, "/tmp/export"), (RUN_ID, "a/b")])
def test_unsafe_identity_is_rejected(fixture, run_id, name):
    project, _, _ = fixture
    with pytest.raises(exporter.EvidenceExportError):
        exporter.export_run(project, run_id, name)


def test_source_path_escape_is_rejected_before_read(fixture):
    project, directory, report = fixture
    report["candidates"][0]["attempts"][0]["code_path"] = "../../../.env"
    write_json(directory / "report.json", report)
    with pytest.raises(exporter.EvidenceExportError, match="unsafe"):
        exporter.export_run(project, RUN_ID, "escape")
    assert not (project / "examples/evidence/escape").exists()


def test_source_symlink_outside_project_is_rejected(fixture, tmp_path):
    project, directory, report = fixture
    source = directory / report["candidates"][0]["attempts"][0]["code_path"]
    outside = tmp_path / "model.py"
    outside.write_text("outside content")
    source.unlink()
    source.symlink_to(outside)
    with pytest.raises(exporter.EvidenceExportError, match="outside"):
        exporter.export_run(project, RUN_ID, "symlink")


def test_destination_symlink_escape_is_rejected(fixture, tmp_path):
    project, _, _ = fixture
    (project / "examples").mkdir()
    (project / "examples/evidence").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(exporter.EvidenceExportError, match="outside"):
        exporter.export_run(project, RUN_ID, "outside")


@pytest.mark.parametrize("location", ["report", "code", "verification", "note"])
def test_credential_like_content_aborts_without_echoing(fixture, location):
    project, directory, report = fixture
    secret = "sk-" + "a" * 32
    note = ""
    if location == "report":
        report["description"] = secret
        write_json(directory / "report.json", report)
    elif location == "code":
        source = directory / report["candidates"][0]["attempts"][0]["code_path"]
        source.write_text("# " + secret)
    elif location == "verification":
        source = directory / report["candidates"][0]["attempts"][0]["code_path"]
        write_json(source.parent / "verification.json", {"authorization": "private fixture token"})
    else:
        note = secret
    with pytest.raises(exporter.EvidenceExportError) as error:
        exporter.export_run(project, RUN_ID, "credential", note)
    assert secret not in str(error.value)
    assert not (project / "examples/evidence/credential").exists()


def test_source_hash_mismatch_aborts(fixture):
    project, directory, report = fixture
    source = directory / report["candidates"][0]["attempts"][0]["code_path"]
    source.write_text("# modified after verification")
    with pytest.raises(exporter.EvidenceExportError, match="SHA256"):
        exporter.export_run(project, RUN_ID, "tampered")


@pytest.mark.parametrize("mode", ["none", "bearer"])
def test_public_provider_authentication_mode_is_not_a_credential(fixture, mode):
    project, directory, report = fixture
    report["provider_metadata"] = {"authorization": mode}
    write_json(directory / "report.json", report)
    result = exporter.export_run(project, RUN_ID, "metadata")
    public = json.loads((project / result["directory"] / "report.json").read_text())
    assert public["provider_metadata"] == {"authorization": mode}


@pytest.mark.parametrize("extra", [
    {"provider_metadata": {"authorization": "Bearer private fixture header"}},
    {"authorization": "none"},
    {"provider_metadata": {"api_key": "none"}},
    {"other": {"provider_metadata": {"authorization": "none"}}},
])
def test_auth_mode_exception_is_limited_to_exact_path_and_enum(fixture, extra):
    project, directory, report = fixture
    report.update(extra)
    write_json(directory / "report.json", report)
    with pytest.raises(exporter.EvidenceExportError):
        exporter.export_run(project, RUN_ID, "blocked_metadata")
    assert not (project / "examples/evidence/blocked_metadata").exists()


def test_existing_bundle_is_not_overwritten(fixture):
    project, _, _ = fixture
    exporter.export_run(project, RUN_ID, "immutable")
    with pytest.raises(exporter.EvidenceExportError, match="already exists"):
        exporter.export_run(project, RUN_ID, "immutable")


def test_failed_generation_with_no_artifact_is_not_fabricated(fixture):
    project, directory, report = fixture
    report["candidates"] = [{"candidate_id": "no_code", "status": "failed", "attempts": [], "metrics": {}}]
    report["status"] = "failed"
    report["selected_candidate_id"] = None
    write_json(directory / "report.json", report)
    result = exporter.export_run(project, RUN_ID, "no_code")
    destination = project / result["directory"]
    metadata = json.loads((destination / "candidates/no_code/metadata.json").read_text())
    assert metadata["code_available"] is False
    assert not (destination / "candidates/no_code/model.py").exists()


def test_standalone_cli_uses_temp_fixture_without_loading_env(fixture):
    project, _, _ = fixture
    result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(project), "--run-id", RUN_ID,
                             "--name", "standalone", "--note", "Offline fixture"],
                            text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["directory"] == "examples/evidence/standalone"
