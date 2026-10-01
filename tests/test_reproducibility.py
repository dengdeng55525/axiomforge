"""Read-only run artifact manifests keep evidence verifiable without exposing contents."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from capability_factory.reproducibility import build_reproducibility


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_manifest_hashes_expected_evidence_and_groups_schema_versions(tmp_path):
    run_dir = tmp_path / "runs" / ("a" * 32)
    _write(run_dir / "dataset" / "manifest.json", json.dumps({"schema_version": "dataset-1"}))
    for relative in (
        "dataset/evaluator/validation_labels.json",
        "dataset/worker/train.json",
        "dataset/worker/validation_features.json",
    ):
        _write(run_dir / relative, "{}")
    code = "def build_pipeline():\n    return None\n"
    _write(run_dir / "candidates" / "c1" / "attempt_0" / "model.py", code)
    for filename in ("constructor_plan.json", "model_metadata.json", "predictions.json", "validation_result.json"):
        _write(run_dir / "candidates" / "c1" / "attempt_0" / filename, "{}")
    _write(run_dir / "candidates" / "c1" / "attempt_0" / "verification.json", '{"status":"passed"}')
    _write(run_dir / "report.json", json.dumps({"schema_version": "1.0"}))
    _write(run_dir / "report.md", "# report\n")
    _write(run_dir / "report.html", "<!doctype html>")
    _write(run_dir / "progress.json", "{}")
    report = {
        "schema_version": "1.0",
        "run_id": "a" * 32,
        "candidates": [{
            "candidate_id": "c1",
            "code_path": "candidates/c1/attempt_0/model.py",
            "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "attempts": [{"code_path": "candidates/c1/attempt_0/model.py"}],
        }],
    }

    result = build_reproducibility(report, run_dir)

    assert result["status"] == "complete"
    assert result["hash_algorithm"] == "sha256"
    assert result["missing_expected_paths"] == []
    assert {item["kind"] for item in result["artifacts"]} == {"input", "code", "validation", "report"}
    model = next(item for item in result["artifacts"] if item["path"].endswith("model.py"))
    assert model["sha256"] == hashlib.sha256(code.encode()).hexdigest()
    assert model["matches_recorded"] is True
    assert model["schema_version"] is None
    dataset = next(item for item in result["artifacts"] if item["path"] == "dataset/manifest.json")
    assert dataset["schema_version"] == "dataset-1"
    assert all("/" not in item["path"] or not item["path"].startswith("/") for item in result["artifacts"])

    _write(run_dir / "candidates" / "c1" / "attempt_0" / "model.py", code + "# changed\n")
    changed = build_reproducibility(report, run_dir)
    assert changed["status"] == "failed"
    assert changed["mismatched_paths"] == ["candidates/c1/attempt_0/model.py"]


def test_manifest_is_partial_for_missing_or_oversized_expected_files(tmp_path):
    run_id = "b" * 32
    run_dir = tmp_path / run_id
    _write(run_dir / "dataset" / "manifest.json", "{}")
    report = {"run_id": run_id, "schema_version": "1.0", "candidates": []}

    result = build_reproducibility(report, run_dir, max_bytes=1)

    assert result["status"] == "partial"
    assert "report.json" in result["missing_expected_paths"]
    manifest = next(item for item in result["artifacts"] if item["path"] == "dataset/manifest.json")
    assert manifest["sha256"] is None
    assert manifest["error"] == "file_size_limit"


def test_manifest_does_not_follow_symlink_or_include_llm_transcripts(tmp_path):
    run_id = "c" * 32
    run_dir = tmp_path / run_id
    _write(run_dir / "report.json", "{}")
    _write(run_dir / "llm" / "01_coder.request.json", '{"secret":"should not be listed"}')
    outside = tmp_path / "outside.py"
    _write(outside, "secret = True")
    (run_dir / "candidates").mkdir(parents=True, exist_ok=True)
    (run_dir / "candidates" / "outside.py").symlink_to(outside)

    result = build_reproducibility({"run_id": run_id}, run_dir)

    paths = {item["path"] for item in result["artifacts"]}
    assert "llm/01_coder.request.json" not in paths
    assert "candidates/outside.py" not in paths
    assert all("secret" not in json.dumps(item) for item in result["artifacts"])


def test_manifest_ignores_report_paths_outside_candidate_allowlist(tmp_path):
    run_id = "f" * 32
    run_dir = tmp_path / run_id
    _write(run_dir / "report.json", "{}")
    report = {
        "run_id": run_id,
        "candidates": [{"code_path": "../../private/secret.py"},
                        {"code_path": "candidates/c1/attempt_0/secret.py"}],
    }
    result = build_reproducibility(report, run_dir)
    paths = {item["path"] for item in result["artifacts"]}
    assert all("private" not in path and "secret" not in path for path in paths)
    assert not any(item["kind"] == "code" for item in result["artifacts"])


def test_manifest_enforces_total_byte_budget(tmp_path):
    run_id = "0" * 32
    run_dir = tmp_path / run_id
    _write(run_dir / "report.json", "x" * 3)
    _write(run_dir / "report.md", "y" * 3)
    result = build_reproducibility({"run_id": run_id}, run_dir, max_total_bytes=4)
    assert result["total_bytes_hashed"] <= 4
    assert result["status"] == "partial"
    assert "report.md" in result["error_paths"]


def test_manifest_rejects_symlinked_run_root(tmp_path):
    actual = tmp_path / "actual"
    _write(actual / "report.json", "{}")
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    result = build_reproducibility({"run_id": "1" * 32}, linked)
    assert result["status"] == "partial"
    assert all(item.get("error") == "symlink_ancestor" for item in result["artifacts"])


def test_failed_attempt_can_be_complete_without_optional_worker_outputs(tmp_path):
    run_id = "2" * 32
    run_dir = tmp_path / run_id
    for relative in (
        "dataset/evaluator/validation_labels.json",
        "dataset/manifest.json",
        "dataset/worker/train.json",
        "dataset/worker/validation_features.json",
        "report.json",
        "report.html",
        "report.md",
        "progress.json",
    ):
        _write(run_dir / relative, "{}")
    _write(run_dir / "candidates/c1/attempt_0/model.py", "def broken_pipeline():\n    return None\n")
    _write(run_dir / "candidates/c1/attempt_0/verification.json", '{"status":"failed"}')
    result = build_reproducibility({
        "run_id": run_id,
        "candidates": [{"candidate_id": "c1", "status": "failed",
                        "code_path": "candidates/c1/attempt_0/model.py"}],
    }, run_dir)
    assert result["status"] == "complete"
    assert result["missing_paths"] == []
    assert any(path.endswith("predictions.json") for path in result["optional_missing_paths"])


def test_fifo_artifact_returns_without_blocking(tmp_path):
    run_id = "3" * 32
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    import os

    os.mkfifo(run_dir / "report.json")
    code = (
        "from capability_factory.reproducibility import build_reproducibility; "
        f"print(build_reproducibility({{'run_id':'{run_id}'}}, r'{run_dir}')['status'])"
    )
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=2,
                               cwd=Path(__file__).parents[1])
    assert completed.returncode == 0
    assert completed.stdout.strip() == "partial"


def test_verify_run_cli_writes_manifest_without_touching_run(tmp_path):
    run_id = "e" * 32
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    _write(run_dir / "report.json", json.dumps({"run_id": run_id, "schema_version": "1.0", "candidates": []}))
    output = tmp_path / "out" / "manifest.json"
    command = [
        sys.executable,
        "scripts/verify_run.py",
        "--project-root",
        str(tmp_path),
        "--run-id",
        run_id,
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert completed.returncode == 1  # partial: the fixture has no dataset/report siblings
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id
    assert not (run_dir / "knowledge.sqlite3").exists()


def test_verify_run_cli_refuses_existing_or_run_directory_outputs(tmp_path):
    run_id = "4" * 32
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    _write(run_dir / "report.json", json.dumps({"run_id": run_id, "candidates": []}))
    existing = tmp_path / "already.json"
    _write(existing, "keep")
    command = [sys.executable, "scripts/verify_run.py", "--project-root", str(tmp_path), "--run-id", run_id]
    for target in (existing, run_dir / "report.json"):
        completed = subprocess.run(command + ["--output", str(target)], cwd=Path(__file__).parents[1],
                                   capture_output=True, text=True)
        assert completed.returncode == 2
        if target == existing:
            assert target.read_text(encoding="utf-8") == "keep"

    outside_target = tmp_path / "link.json"
    outside_target.symlink_to(existing)
    completed = subprocess.run(command + ["--output", str(outside_target)], cwd=Path(__file__).parents[1],
                               capture_output=True, text=True)
    assert completed.returncode == 2
    assert existing.read_text(encoding="utf-8") == "keep"
