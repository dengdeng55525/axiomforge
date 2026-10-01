"""Read-only, deterministic quality gates for source-grounded capability memory.

The exported report records independently inspectable checks, never an invented
quality score.  ``validate_snapshot`` is pure; the SQLite adapters take one read
transaction and never call a model, execute source code or write knowledge.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from typing import Any

from .ingestion import TABULAR, TEXT

SCHEMA_VERSION = "knowledge-quality.v1"
ALLOWED_STATUSES = {"draft", "extracted", "verified", "deprecated"}
ALLOWED_RELATIONS = {
    "SOLVES", "IMPLEMENTS", "USES", "REQUIRES", "DERIVED_FROM", "EVALUATED_ON",
    "EVALUATES", "MEASURED_BY", "REPAIRS", "SUPERSEDES", "AVOIDED_BY",
}
_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
_TASKS = {TABULAR, TEXT}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, allow_nan=False)


def _digest_card(card: Mapping[str, Any]) -> str:
    content = dict(card)
    for key in ("version", "created_at", "node_id", "score", "id"):
        content.pop(key, None)
    return hashlib.sha256(_json(content).encode()).hexdigest()


def _object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError, RecursionError):
            return None
    return dict(value) if isinstance(value, Mapping) else None


def _positive_version(value: Any) -> bool:
    # SQLite integers are signed 64-bit.  Booleans and numeric strings cannot
    # silently become revisions, and no untrusted value is used to build range().
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value < 2**63


def validate_snapshot(*, cards: Any = None, sources: Any = None, versions: Any = None,
                      graph: Any = None, failures: Any = None, runs: Any = None,
                      run_revisions: Any = None) -> dict[str, Any]:
    """Check a portable snapshot, returning structured facts for every gate.

    Version rows use ``card`` or ``card_json`` plus the corresponding SQLite
    columns.  Source rows use ``source`` or ``source_json``; plain source objects
    are accepted too.  Verified runtime experiences additionally require the
    matching validated failure and a persisted successful run/repair snapshot.
    Malformed exported records become issues instead of interrupting the audit.
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def problem(check: str, reason: str, **details: Any) -> None:
        grouped[check].append({"error": reason, **details})

    def rows(value: Any, label: str) -> list[dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, (list, tuple)):
            problem("snapshot_shape", "expected_array", field=label)
            return []
        result = []
        for index, row in enumerate(value):
            if not isinstance(row, Mapping):
                problem("snapshot_shape", "expected_object", field=label, index=index)
            else:
                result.append(dict(row))
        return result

    latest = rows(cards, "cards")
    version_rows = rows(versions, "versions")
    if versions is None:
        version_rows = [{"capability_id": c.get("capability_id", c.get("id")),
                         "version": c.get("version"), "card": c,
                         "content_sha256": c.get("content_sha256")} for c in latest]
    source_rows = rows(sources, "sources")
    graph = _object(graph) if graph is not None else {}
    if graph is None:
        problem("snapshot_shape", "expected_object", field="graph")
        graph = {}
    nodes, edges = rows(graph.get("nodes"), "nodes"), rows(graph.get("edges"), "edges")
    failure_rows = rows(failures, "failures")
    run_rows = rows(runs, "runs") + rows(run_revisions, "run_revisions")

    source_map: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        source = _object(row.get("source", row.get("source_json", row)))
        if source is None:
            problem("source_record_shape", "malformed_source_json", source_id=row.get("source_id"))
            continue
        sid = source.get("source_id")
        if not isinstance(sid, str) or not sid:
            problem("source_record_shape", "missing_source_id")
            continue
        if sid in source_map:
            problem("source_record_shape", "duplicate_source_id", source_id=sid)
        source_map[sid] = source
        for field in ("source_id", "source_key", "content_sha256"):
            if field in row and row[field] != source.get(field):
                problem("source_record_shape", "source_column_mismatch", source_id=sid, field=field)
        if (not _HEX64.fullmatch(str(source.get("content_sha256", "")))
                or not isinstance(source.get("uri"), str) or not source["uri"]
                or not isinstance(source.get("license"), str) or not source["license"]
                or not isinstance(source.get("locator"), Mapping) or not source["locator"]):
            problem("source_record_shape", "invalid_source_provenance", source_id=sid)

    node_ids: set[str] = set()
    for node in nodes:
        identity = node.get("id", node.get("node_id"))
        if not isinstance(identity, str) or not identity:
            problem("graph_reference_integrity", "missing_node_id")
        elif identity in node_ids:
            problem("graph_reference_integrity", "duplicate_node_id", node_id=identity)
        else:
            node_ids.add(identity)
    edge_keys: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.get("source", edge.get("source_id")),
               edge.get("target", edge.get("target_id")), edge.get("relation"))
        if any(not isinstance(part, str) for part in key):
            problem("graph_reference_integrity", "invalid_edge_fields")
            continue
        source, target, relation = key
        if source not in node_ids or target not in node_ids:
            problem("graph_reference_integrity", "dangling_node_reference", source=source, target=target)
        if relation not in ALLOWED_RELATIONS:
            problem("graph_reference_integrity", "unknown_relation", relation=relation)
        if key in edge_keys:
            problem("graph_reference_integrity", "duplicate_edge", source=source, target=target, relation=relation)
        edge_keys.add(key)

    by_capability: dict[str, list[int]] = defaultdict(list)
    hash_locations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    normalised_cards: list[tuple[str, int, dict[str, Any]]] = []
    for row in version_rows:
        card = _object(row.get("card", row.get("card_json")))
        identity, version = row.get("capability_id"), row.get("version")
        if not isinstance(identity, str) or not identity or not _positive_version(version):
            problem("version_record_shape", "invalid_identity_or_version", capability_id=identity, version=version)
            continue
        by_capability[identity].append(version)
        location = {"capability_id": identity, "version": version}
        if card is None:
            problem("version_record_shape", "malformed_card_json", **location)
            continue
        normalised_cards.append((identity, version, card))
        for field, expected in (("capability_id", identity), ("version", version),
                                ("status", row.get("status", card.get("status"))),
                                ("origin", row.get("origin", card.get("origin")))):
            if card.get(field) != expected:
                problem("version_record_shape", "card_column_mismatch", field=field, **location)
        if "id" in card and card["id"] != identity:
            problem("version_record_shape", "card_column_mismatch", field="id", **location)
        status, tasks = card.get("status"), card.get("task_types")
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            problem("card_status_task_contract", "invalid_status", **location)
        if (not isinstance(tasks, list) or not tasks
                or any(not isinstance(task, str) or task not in _TASKS for task in tasks)):
            problem("card_status_task_contract", "invalid_task_types", **location)
        evidence = card.get("evidence", card.get("source_ids"))
        if not isinstance(evidence, list) or not evidence:
            problem("source_citations", "missing_evidence", **location)
            evidence = []
        cited = set()
        for reference in evidence:
            sid = reference if isinstance(reference, str) else reference.get("source_id") if isinstance(reference, Mapping) else None
            if not isinstance(sid, str) or not sid or sid in cited:
                problem("source_citations", "duplicate_or_missing_source_id", **location)
                continue
            cited.add(sid)
            source = source_map.get(sid)
            if source is None:
                problem("source_citations", "unknown_source", source_id=sid, **location)
            elif isinstance(reference, Mapping):
                for field in ("content_sha256", "revision", "uri", "locator", "license"):
                    if field in reference and reference[field] != source.get(field):
                        problem("source_citations", "evidence_metadata_mismatch", field=field, source_id=sid, **location)
        digest = row.get("content_sha256")
        if isinstance(digest, str) and _HEX64.fullmatch(digest):
            hash_locations[digest].append(location)
        try:
            matches = isinstance(digest, str) and _HEX64.fullmatch(digest) and _digest_card(card) == digest
        except (ValueError, TypeError, RecursionError):
            matches = False
        if not matches:
            problem("content_hash_integrity", "content_hash_mismatch", **location)

        node = f"capability:{identity}:v{version}"
        expected_edges = [(node, sid, "DERIVED_FROM") for sid in cited]
        expected_edges += [(node, f"task:{task}", "SOLVES") for task in tasks if isinstance(task, str)] if isinstance(tasks, list) else []
        if version > 1:
            expected_edges.append((node, f"capability:{identity}:v{version - 1}", "SUPERSEDES"))
        for source, target, relation in expected_edges:
            if (source, target, relation) not in edge_keys:
                problem("graph_semantics", "missing_lineage_edge", source=source, target=target, relation=relation)

    for identity, revisions in by_capability.items():
        ordered = sorted(revisions)
        # Enumerate actual records only; a malicious 2**62 version uses O(n)
        # memory and time, never a materialised range through that revision.
        if any(version != index for index, version in enumerate(ordered, start=1)):
            problem("version_continuity", "version_sequence_gap", capability_id=identity, versions=ordered[:25])
    duplicates = {digest: locations for digest, locations in hash_locations.items() if len(locations) > 1}
    for digest, locations in duplicates.items():
        problem("duplicate_content", "duplicate_content_hash", content_sha256=digest, versions=locations[:25])

    # Validated experience must be tied to the persisted failure and to an
    # actual passed run or passed candidate containing the same repair.
    failure_map: dict[str, dict[str, Any]] = {}
    for row in failure_rows:
        experience = _object(row.get("experience", row.get("experience_json", row)))
        fid = row.get("failure_id")
        if experience is None or not isinstance(fid, str):
            problem("verified_experience_evidence", "malformed_failure_record")
            continue
        failure_map[fid] = {**row, "experience": experience}
    run_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in run_rows:
        report = _object(row.get("report", row.get("report_json", row)))
        rid = row.get("run_id")
        if report is not None and isinstance(rid, str):
            run_map[rid].append(report)
    for identity, version, card in normalised_cards:
        if card.get("status") != "verified" or card.get("origin") != "runtime_experience":
            continue
        validation_runs = card.get("validation_runs")
        if (not isinstance(validation_runs, list) or not validation_runs
                or any(not isinstance(run_id, str) or not run_id for run_id in validation_runs)):
            problem("verified_experience_evidence", "invalid_validation_runs",
                    capability_id=identity, version=version)
            continue
        evidence = card.get("evidence", [])
        evidence = evidence if isinstance(evidence, list) else []
        linked = False
        for reference in evidence:
            sid = reference if isinstance(reference, str) else reference.get("source_id") if isinstance(reference, Mapping) else None
            source = source_map.get(sid) if isinstance(sid, str) else None
            locator = source.get("locator", {}) if source else {}
            if not isinstance(locator, Mapping):
                continue
            fid, rid = locator.get("failure_id"), locator.get("run_id")
            failure = failure_map.get(fid) if isinstance(fid, str) else None
            if (failure is None or failure.get("validated") not in (1, True)
                    or failure.get("run_id") != rid or source.get("kind") != "validation_run"
                    or not isinstance(rid, str) or source.get("uri") != f"run://{rid}"):
                continue
            experience = failure["experience"]
            if (experience.get("validated") is not True or experience.get("failure_id") != fid
                    or experience.get("run_id") != rid or rid not in validation_runs):
                continue
            for report in run_map.get(rid, []):
                try:
                    digest = hashlib.sha256(_json(report).encode()).hexdigest()
                except (ValueError, TypeError, RecursionError):
                    problem("verified_experience_evidence", "invalid_validation_report",
                            capability_id=identity, version=version, run_id=rid)
                    continue
                if digest != source.get("content_sha256") or digest != source.get("revision"):
                    continue
                candidates = report.get("candidates", [])
                candidates = candidates if isinstance(candidates, list) else []
                repaired = any(isinstance(candidate, Mapping) and candidate.get("status") == "passed"
                               and isinstance(candidate.get("repairs"), list) and any(
                                   isinstance(repair, Mapping) and all(repair.get(key) == experience.get(key)
                                   for key in ("error_type", "diagnosis", "fix"))
                                   for repair in candidate["repairs"])
                               for candidate in candidates)
                if repaired:
                    linked = True
        if not linked:
            problem("verified_experience_evidence", "verified_experience_missing_validation",
                    capability_id=identity, version=version)

    for card in latest:
        identity, version = card.get("capability_id", card.get("id")), card.get("version")
        if isinstance(identity, str) and identity in by_capability and version != max(by_capability[identity]):
            problem("latest_view_consistency", "latest_view_stale", capability_id=identity)

    titles = {
        "snapshot_shape": "Snapshot fields contain well-formed records",
        "source_record_shape": "Sources have unique IDs, hashes, licenses and locators",
        "version_record_shape": "Stored columns match capability IDs, versions and state",
        "card_status_task_contract": "Statuses and task types follow the governed vocabulary",
        "source_citations": "Capability citations match stored source evidence",
        "version_continuity": "Immutable versions are contiguous from v1",
        "content_hash_integrity": "Canonical content matches the stored SHA-256",
        "duplicate_content": "Content hashes identify unique capability revisions",
        "graph_reference_integrity": "Graph nodes and edges are unique and valid",
        "graph_semantics": "Task, source and predecessor lineage edges are present",
        "verified_experience_evidence": "Verified experiences have persisted successful validation",
        "latest_view_consistency": "Latest cards match immutable revision history",
    }
    warning_checks = {"graph_semantics", "latest_view_consistency"}
    empty = not version_rows
    checks, issues, warnings = [], [], []
    for check_id, message in titles.items():
        examples = grouped.get(check_id, [])
        severity = "warning" if check_id in warning_checks else "error"
        status = ("warning" if severity == "warning" else "failed") if examples else "not_evaluated" if empty else "passed"
        checks.append({"id": check_id, "status": status, "severity": severity, "message": message,
                       "issue_count": len(examples)})
        if examples:
            issue = {"code": check_id, "severity": severity, "message": message,
                     "details": {"count": len(examples), "examples": examples[:30]}}
            (warnings if severity == "warning" else issues).append(issue)
    evaluated = sum(check["status"] != "not_evaluated" for check in checks)
    passed = sum(check["status"] == "passed" for check in checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "failed" if issues else "empty" if empty else "passed",
        "summary": {"cards": len(latest), "versions": len(version_rows), "sources": len(source_rows),
                    "nodes": len(nodes), "edges": len(edges), "checks": len(checks),
                    "checks_evaluated": evaluated, "checks_passed": passed,
                    "checks_passed_ratio": passed / evaluated if evaluated else None,
                    "errors": len(issues), "warnings": len(warnings)},
        "checks": checks, "issues": issues, "warnings": warnings,
        "duplicate_content_groups": duplicates,
    }


def _snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    """Acquire all tables in the same deferred SQLite read transaction."""
    connection.execute("BEGIN")

    def records(table: str) -> list[dict[str, Any]]:
        cursor = connection.execute(f"SELECT * FROM {table}")
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor]

    versions = records("cf_capability_versions")
    latest: dict[str, dict[str, Any]] = {}
    for row in versions:
        identity, version = row["capability_id"], row["version"]
        if _positive_version(version) and (identity not in latest or version > latest[identity]["version"]):
            latest[identity] = row
    cards = [_object(row["card_json"]) for row in latest.values()]
    return {"cards": cards, "versions": versions, "sources": records("cf_sources"),
            "graph": {"nodes": records("cf_nodes"), "edges": records("cf_edges")},
            "failures": records("cf_failures"), "runs": records("cf_runs"),
            "run_revisions": records("cf_run_revisions")}


def validate_store(store: Any) -> dict[str, Any]:
    """Audit a KnowledgeStore, including its existing in-memory connection."""
    with store._connection() as connection:
        return validate_snapshot(**_snapshot(connection))


def validate_database(database: str | Path) -> dict[str, Any]:
    """Open an existing SQLite file in URI read-only mode; never initialise it."""
    path = Path(database).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("Knowledge database must be an existing regular file")
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        return validate_snapshot(**_snapshot(connection))


__all__ = ["SCHEMA_VERSION", "validate_snapshot", "validate_store", "validate_database"]
