"""Committed-source provenance, AST isolation and immutable knowledge history."""

import json
import subprocess

import pytest
from typer.testing import CliRunner

from capability_factory.cli import app
from capability_factory.ingestion import TABULAR
from capability_factory.knowledge import KnowledgeStore
from capability_factory.repository import extract_repository


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "source"
    path.mkdir()
    git(path, "init")
    git(path, "config", "user.name", "Test fixture")
    git(path, "config", "user.email", "fixture@example.invalid")
    (path / "algorithm.py").write_text(
        'import numpy as np\nraise RuntimeError("source must never execute")\n'
        'def predict(values: list) -> list:\n    """Return calibrated probabilities."""\n    return values\n'
        'class Encoder:\n    """Encode features."""\n    def transform(self, values):\n        return values\n'
    )
    git(path, "add", "algorithm.py")
    git(path, "commit", "-m", "fixture baseline")
    return path


def extract(repository, paths=None, **kwargs):
    return extract_repository(repository, paths or ["algorithm.py"],
                              repository_url="https://github.com/example/fixture",
                              license_id="MIT", task_types=[TABULAR], **kwargs)


def test_git_blobs_ignore_worktree_and_never_execute_source(repository):
    commit = git(repository, "rev-parse", "HEAD")
    (repository / "algorithm.py").write_text("def forged(): pass")
    result = extract(repository)
    assert result["commit"] == commit
    assert result["source_executed"] is False
    assert {c["name"] for c in result["capabilities"]} == {"predict", "Encoder", "Encoder.transform"}
    card = result["capabilities"][0]
    assert card["dependencies"] == ["import numpy as np"]
    assert card["output_schema"]["annotation"] == "list"
    assert all(commit in source["uri"] for source in result["sources"])
    assert result == extract(repository, revision=commit)


def test_repository_ingestion_versions_and_retrieval(repository, tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    first = extract(repository)
    assert store.ingest_repository(first)["new_capability_versions"] == 3
    assert store.ingest_repository(first)["new_capability_versions"] == 0
    (repository / "algorithm.py").write_text(
        'def predict(values: list) -> list:\n    """Return corrected probabilities."""\n    return values\n'
    )
    git(repository, "add", "algorithm.py")
    git(repository, "commit", "-m", "fixture revision")
    second = extract(repository)
    assert second["capabilities"][0]["capability_id"] == first["capabilities"][0]["capability_id"]
    assert store.ingest_repository(second)["new_capability_versions"] == 1
    card = next(c for c in store.list_capabilities() if c["name"] == "predict")
    assert card["version"] == 2 and card["status"] == "extracted"
    assert card["origin"] == "repository_ast"
    assert card["id"] in {c["id"] for c in store.search("corrected probabilities", TABULAR)}
    graph = store.graph()
    assert any(edge["relation"] == "SUPERSEDES" for edge in graph["edges"])
    assert {node["properties"]["revision"] for node in graph["nodes"] if node["kind"] == "Source"} == {first["commit"], second["commit"]}


@pytest.mark.parametrize("path", ["../algorithm.py", "/tmp/algorithm.py", "./algorithm.py", "secret.env", "a:evil.py", "missing.py"])
def test_paths_are_explicit_committed_python_files(repository, path):
    with pytest.raises(ValueError):
        extract(repository, [path])


def test_symlinks_and_oversized_blobs_rejected(repository):
    (repository / "link.py").symlink_to("/etc/passwd")
    (repository / "large.py").write_text("#" * (256 * 1024 + 1))
    git(repository, "add", "link.py", "large.py")
    git(repository, "commit", "-m", "untrusted fixture")
    with pytest.raises(ValueError, match="symlinks"):
        extract(repository, ["link.py"])
    with pytest.raises(ValueError, match="256 KiB"):
        extract(repository, ["large.py"])


def test_source_urls_never_accept_credentials(repository):
    with pytest.raises(ValueError, match="credential-free"):
        extract_repository(repository, ["algorithm.py"],
                           repository_url="https://user:secret@github.com/example/repo",
                           license_id="MIT", task_types=[TABULAR])


def test_cli_ingestion_and_offline_openapi(repository, tmp_path, monkeypatch):
    root = tmp_path / "application"
    root.mkdir()
    monkeypatch.setenv("ALGOFORGE_ROOT", str(root))
    runner = CliRunner()
    target = tmp_path / "manifest.json"
    result = runner.invoke(app, ["ingest-repo", str(repository), "--path", "algorithm.py",
                                "--repository-url", "https://github.com/example/repo",
                                "--license", "MIT", "--task-type", TABULAR, "--output", str(target)])
    assert result.exit_code == 0, result.output
    assert json.loads(target.read_text())["source_executed"] is False
    db = root / "artifacts/knowledge.sqlite3"
    before = db.read_bytes()
    api_path = tmp_path / "openapi.json"
    result = runner.invoke(app, ["export-openapi", "--output", str(api_path)])
    assert result.exit_code == 0, result.output
    api = json.loads(api_path.read_text())
    assert "/runs" in api["paths"]
    assert "RunRequest" in api["components"]["schemas"]
    assert db.read_bytes() == before
