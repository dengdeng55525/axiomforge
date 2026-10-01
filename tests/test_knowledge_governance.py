"""Regression tests for the read-only knowledge quality gate."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from capability_factory.knowledge import KnowledgeStore
from capability_factory.knowledge_governance import (
    validate_database,
    validate_snapshot,
    validate_store,
)

ROOT = Path(__file__).resolve().parents[1]


def _store(tmp_path: Path) -> KnowledgeStore:
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    store.initialize()
    result = store.ingest_sources(ROOT)
    assert result["issues"] == []
    return store


def test_valid_knowledge_store_passes_quality_gate(tmp_path):
    store = _store(tmp_path)
    try:
        report = validate_store(store)
    finally:
        store.close()
    assert report["status"] == "passed"
    assert report["summary"]["errors"] == 0
    assert report["summary"]["checks_passed_ratio"] == 1.0
    assert report["summary"]["versions"] >= 12
    assert {check["id"] for check in report["checks"]} >= {
        "source_citations", "version_continuity", "content_hash_integrity", "graph_reference_integrity",
    }


def test_missing_source_and_invalid_task_are_actionable():
    card = {
        "capability_id": "broken-card", "version": 1, "status": "published",
        "task_types": ["image_classification"], "evidence": ["missing-source"],
        "summary": "broken",
    }
    report = validate_snapshot(cards=[card], versions=[{"capability_id": "broken-card", "version": 1,
                                                         "content_sha256": "a" * 64, "card": card}])
    assert report["status"] == "failed"
    codes = {issue["code"] for issue in report["issues"]}
    assert {"source_citations", "card_status_task_contract"} <= codes
    source_check = next(check for check in report["checks"] if check["id"] == "source_citations")
    assert source_check["status"] == "failed"


def test_evidence_hash_mismatch_is_reported():
    source = {
        "source_id": "src-1", "uri": "https://example.invalid/source", "license": "CC0",
        "revision": "r1", "content_sha256": "a" * 64, "locator": {"path": "source.md"},
    }
    card = {
        "capability_id": "hash-card", "version": 1, "status": "extracted",
        "task_types": ["tabular_binary_classification"],
        "evidence": [{"source_id": "src-1", "content_sha256": "b" * 64}],
        "summary": "hash mismatch",
    }
    report = validate_snapshot(
        cards=[card],
        sources=[source],
        versions=[{"capability_id": "hash-card", "version": 1,
                   "content_sha256": "c" * 64, "card": card}],
    )
    issue = next(item for item in report["issues"] if item["code"] == "source_citations")
    assert any(example["error"] == "evidence_metadata_mismatch" for example in issue["details"]["examples"])


def test_version_gap_and_duplicate_content_are_detected():
    card_a = {"capability_id": "a", "version": 1, "status": "extracted",
              "task_types": [], "evidence": [], "summary": "a"}
    card_b = {"capability_id": "a", "version": 3, "status": "extracted",
              "task_types": [], "evidence": [], "summary": "b"}
    same_hash = "b" * 64
    report = validate_snapshot(
        versions=[
            {"capability_id": "a", "version": 1, "content_sha256": same_hash, "card": card_a},
            {"capability_id": "other", "version": 1, "content_sha256": same_hash, "card": card_b},
        ]
    )
    codes = {issue["code"] for issue in report["issues"]}
    assert "duplicate_content" in codes
    # The malformed task/evidence records add contract issues, while the
    # revision sequence remains independently visible in the report.
    report_with_gap = validate_snapshot(
        versions=[
            {"capability_id": "a", "version": 1, "content_sha256": same_hash, "card": card_a},
            {"capability_id": "a", "version": 3, "content_sha256": "c" * 64, "card": card_b},
        ]
    )
    assert "version_continuity" in {issue["code"] for issue in report_with_gap["issues"]}


def test_graph_dangling_edges_and_unknown_relations_fail():
    report = validate_snapshot(graph={"nodes": [{"id": "n1"}], "edges": [
        {"source": "n1", "target": "missing", "relation": "USES"},
        {"source": "n1", "target": "n1", "relation": "INVENTED"},
    ]})
    assert report["status"] == "failed"
    issue = next(item for item in report["issues"] if item["code"] == "graph_reference_integrity")
    assert issue["details"]["count"] == 2


def test_store_corruption_is_detected_without_mutation(tmp_path):
    store = _store(tmp_path)
    try:
        with sqlite3.connect(store.db_path) as connection:
            row = connection.execute(
                "SELECT capability_id,version,card_json FROM cf_capability_versions LIMIT 1"
            ).fetchone()
            capability_id, version, card_json = row
            card = json.loads(card_json)
            card["summary"] = "tampered after ingestion"
            connection.execute(
                "UPDATE cf_capability_versions SET card_json=? WHERE capability_id=? AND version=?",
                (json.dumps(card, ensure_ascii=False), capability_id, version),
            )
        report = validate_store(store)
    finally:
        store.close()
    assert report["status"] == "failed"
    assert "content_hash_integrity" in {issue["code"] for issue in report["issues"]}


def test_empty_and_malformed_snapshots_are_safe():
    empty = validate_snapshot()
    assert empty["status"] == "empty"
    assert empty["summary"]["checks_passed_ratio"] is None
    malformed = validate_snapshot(
        versions=[
            {"capability_id": "huge", "version": 10**100, "card_json": "{"},
            {"capability_id": "bad", "version": 1, "card_json": "[1, 2]"},
        ],
        graph={"nodes": "not-a-list", "edges": {"bad": True}},
    )
    assert malformed["status"] == "failed"
    codes = {issue["code"] for issue in malformed["issues"]}
    assert {"snapshot_shape", "version_record_shape"} <= codes


def test_database_adapter_is_read_only_and_missing_files_do_not_get_created(tmp_path):
    missing = tmp_path / "missing.sqlite"
    try:
        validate_database(missing)
    except (OSError, ValueError):
        pass
    else:
        raise AssertionError("missing database must be rejected")
    assert not missing.exists()


def test_column_mismatch_and_duplicate_source_or_node_are_reported():
    card = {"capability_id": "one", "version": 1, "status": "extracted",
            "task_types": ["tabular_binary_classification"], "evidence": [], "summary": "x"}
    report = validate_snapshot(
        versions=[{"capability_id": "one", "version": 1, "status": "verified", "origin": "x",
                   "content_sha256": "a" * 64, "card": {**card, "id": "other"}}],
        sources=[{"source_id": "src", "uri": "u", "license": "l", "content_sha256": "b" * 64,
                  "locator": {}}, {"source_id": "src", "uri": "u2", "license": "l", "content_sha256": "c" * 64,
                                    "locator": {}}],
        graph={"nodes": [{"id": "n"}, {"id": "n"}], "edges": []},
    )
    assert "source_record_shape" in {issue["code"] for issue in report["issues"]}
    assert "graph_reference_integrity" in {issue["code"] for issue in report["issues"]}
    assert "version_record_shape" in {issue["code"] for issue in report["issues"]}


def test_validated_runtime_experience_requires_and_preserves_run_evidence(tmp_path):
    store = _store(tmp_path)
    try:
        repair = {"error_type": "MissingInterface", "diagnosis": "builder absent", "fix": "add builder"}
        store.save_run({"run_id": "repair-quality", "status": "passed", "candidates": [
            {"status": "passed", "repairs": [repair]},
        ]})
        store.record_experience("repair-quality", **repair,
                                task_type="text_binary_classification", validated=True)
        report = validate_store(store)
    finally:
        store.close()
    assert report["status"] == "passed"
    assert report["summary"]["checks_passed_ratio"] == 1.0


def test_verified_experience_without_matching_repair_fails_closed():
    run = {"run_id": "run-no-repair", "status": "passed",
           "candidates": [{"status": "passed", "repairs": []}]}
    run_hash = hashlib.sha256(json.dumps(run, ensure_ascii=False, sort_keys=True,
                                        allow_nan=False).encode()).hexdigest()
    source = {"source_id": "src-run", "source_key": "validation:run-no-repair",
              "uri": "run://run-no-repair", "revision": run_hash,
              "content_sha256": run_hash, "license": "original-runtime-evidence",
              "kind": "validation_run", "locator": {"run_id": "run-no-repair", "failure_id": "failure-1"}}
    failure = {"failure_id": "failure-1", "run_id": "run-no-repair", "validated": 1,
               "experience_json": json.dumps({"failure_id": "failure-1", "run_id": "run-no-repair",
                                               "validated": True, "error_type": "E", "diagnosis": "D", "fix": "F"})}
    card = {"capability_id": "repair-card", "version": 1, "id": "repair-card",
            "status": "verified", "origin": "runtime_experience",
            "task_types": ["text_binary_classification"], "summary": "validated repair",
            "evidence": ["src-run"], "validation_runs": ["run-no-repair"]}
    report = validate_snapshot(
        cards=[card],
        versions=[{"capability_id": "repair-card", "version": 1, "status": "verified",
                   "origin": "runtime_experience", "content_sha256": "a" * 64, "card": card}],
        sources=[source], failures=[failure], runs=[{"run_id": "run-no-repair", "report_json": json.dumps(run)}],
    )
    issue = next(item for item in report["issues"] if item["code"] == "verified_experience_evidence")
    assert any(example["error"] == "verified_experience_missing_validation" for example in issue["details"]["examples"])


def test_verified_experience_with_non_list_validation_runs_fails_closed():
    card = {"capability_id": "bad-repair", "version": 1, "status": "verified",
            "origin": "runtime_experience", "task_types": ["text_binary_classification"],
            "summary": "bad validation runs", "evidence": [], "validation_runs": "run-1"}
    report = validate_snapshot(versions=[{"capability_id": "bad-repair", "version": 1,
                                         "status": "verified", "origin": "runtime_experience",
                                         "content_sha256": "a" * 64, "card": card}])
    issue = next(item for item in report["issues"] if item["code"] == "verified_experience_evidence")
    assert any(example["error"] == "invalid_validation_runs" for example in issue["details"]["examples"])


def test_cli_empty_and_output_path_safety(tmp_path):
    database = tmp_path / "empty.sqlite"
    empty_store = KnowledgeStore(database)
    empty_store.initialize()
    empty_store.close()
    script = ROOT / "scripts/validate_knowledge.py"
    empty = subprocess.run([sys.executable, str(script), "--database", str(database)],
                           capture_output=True, text=True)
    assert empty.returncode != 0
    assert json.loads(empty.stdout)["status"] == "empty"

    output = tmp_path / "report.json"
    first = subprocess.run([sys.executable, str(script), "--database", str(database), "--output", str(output)],
                           capture_output=True, text=True)
    assert first.returncode != 0
    original_output = output.read_text(encoding="utf-8")
    assert json.loads(original_output)["status"] == "empty"
    existing = subprocess.run([sys.executable, str(script), "--database", str(database), "--output", str(output)],
                              capture_output=True, text=True)
    assert existing.returncode != 0
    assert output.read_text(encoding="utf-8") == original_output
    hardlink = tmp_path / "database-hardlink.sqlite"
    hardlink.hardlink_to(database)
    blocked = subprocess.run([sys.executable, str(script), "--database", str(database), "--output", str(hardlink)],
                             capture_output=True, text=True)
    assert blocked.returncode != 0
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    linked = subprocess.run([sys.executable, str(script), "--database", str(database),
                             "--output", str(linked_parent / "report.json")],
                            capture_output=True, text=True)
    assert linked.returncode != 0
