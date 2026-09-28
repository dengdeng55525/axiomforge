"""SQLite capability memory with auditable retrieval and immutable revisions."""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import uuid
from collections import deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ingestion import TABULAR, TEXT, collect_sources

TASK_TYPES = {TABULAR, TEXT}
_ASSETS = Path(__file__).resolve().parents[2] / "knowledge"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _tokens(value: str) -> set[str]:
    value = value.lower()
    terms = set(re.findall(r"[a-z0-9_]+", value))
    for chunk in re.findall(r"[\u4e00-\u9fff]+", value):
        terms.add(chunk)
        terms.update(chunk[i:i + 2] for i in range(max(0, len(chunk) - 1)))
    return terms


def _node_id(card: dict[str, Any]) -> str:
    return f"capability:{card['capability_id']}:v{card['version']}"


class KnowledgeStore:
    """Connections are transaction-scoped and safe across API worker threads.

    ``:memory:`` uses a private shared-cache database with an anchor connection;
    regular deployments should pass an on-disk Path. Public mutations use SQLite
    immediate transactions so concurrent event sequences and versions are unique.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._memory = self.db_path == ":memory:"
        self._uri = f"file:capability-{uuid.uuid4().hex}?mode=memory&cache=shared"
        self._anchor: sqlite3.Connection | None = None
        if self._memory:
            self._anchor = sqlite3.connect(self._uri, uri=True, check_same_thread=False)
        else:
            Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        if self._anchor is not None:
            self._anchor.close()
            self._anchor = None

    @contextmanager
    def _connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._uri if self._memory else self.db_path,
                                     uri=self._memory, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        try:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            if not self._memory:
                connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript((_ASSETS / "runtime_schema.sql").read_text())

    @staticmethod
    def _node(connection: sqlite3.Connection, node_id: str, kind: str,
              label: str, properties: dict[str, Any]) -> None:
        connection.execute(
            "INSERT INTO cf_nodes VALUES (?,?,?,?) ON CONFLICT(node_id) DO UPDATE SET "
            "kind=excluded.kind,label=excluded.label,properties_json=excluded.properties_json",
            (node_id, kind, label, _json(properties)),
        )

    @staticmethod
    def _edge(connection: sqlite3.Connection, source: str, target: str,
              relation: str, **properties: Any) -> None:
        edge_id = "edge-" + _digest([source, target, relation])[:24]
        connection.execute(
            "INSERT INTO cf_edges VALUES (?,?,?,?,?) ON CONFLICT(edge_id) DO UPDATE SET "
            "properties_json=excluded.properties_json",
            (edge_id, source, target, relation, _json(properties)),
        )

    def _source(self, connection: sqlite3.Connection, source: dict[str, Any]) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO cf_sources VALUES (?,?,?,?,?)",
            (source["source_id"], source["source_key"], source["content_sha256"], _json(source), _now()),
        )
        self._node(connection, source["source_id"], "Source", source["source_key"], {
            "uri": source["uri"], "revision": source["revision"],
            "locator": source["locator"], "content_sha256": source["content_sha256"],
            "license": source["license"],
        })

    @staticmethod
    def _validate_card(card: dict[str, Any], sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
        card = dict(card)
        identity = card.get("capability_id", card.get("id"))
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", identity):
            raise ValueError("Capability requires a stable alphanumeric capability_id")
        card["capability_id"] = identity
        card["name"] = str(card.get("name", card.get("title", identity)))[:200]
        card["summary"] = str(card.get("summary", card.get("description", "")))[:5000]
        if not card["summary"].strip():
            raise ValueError("Capability summary is required")
        tasks = card.get("task_types", [card.get("task_type")])
        if isinstance(tasks, str):
            tasks = [tasks]
        if not isinstance(tasks, list) or not tasks or not set(tasks) <= TASK_TYPES:
            raise ValueError("Capability task_types must contain supported task types")
        card["task_types"] = sorted(set(tasks))
        references = card.get("evidence", card.get("source_ids", []))
        if not isinstance(references, list) or not references:
            raise ValueError("Capability must cite at least one ingested source")
        evidence = []
        for reference in references:
            source_id = reference if isinstance(reference, str) else reference.get("source_id")
            if source_id not in sources:
                raise ValueError(f"Unknown evidence source: {source_id}")
            source = sources[source_id]
            evidence.append({
                "source_id": source_id, "uri": source["uri"],
                "revision": source["revision"], "content_sha256": source["content_sha256"],
                "locator": source["locator"], "license": source["license"],
            })
        card["evidence"] = evidence
        for field in ("preconditions", "dependencies", "tags", "uses", "related"):
            value = card.get(field, [])
            if not isinstance(value, list):
                raise ValueError(f"{field} must be an array")
            if field != "uses" and any(not isinstance(item, str) for item in value):
                raise ValueError(f"{field} entries must be strings")
            card[field] = value
        normalized_uses = []
        for use in card["uses"]:
            use = {"kind": "Algorithm", "label": use} if isinstance(use, str) else use
            if not isinstance(use, dict) or not isinstance(use.get("label"), str):
                raise ValueError("uses entries require a label string")
            if use.get("kind", "Algorithm") not in {"Algorithm", "Transform", "Metric"}:
                raise ValueError("uses kind must be Algorithm, Transform or Metric")
            if not use["label"].strip() or len(use["label"]) > 200:
                raise ValueError("uses label must contain 1-200 characters")
            normalized_uses.append({"kind": use.get("kind", "Algorithm"), "label": use["label"]})
        card["uses"] = normalized_uses
        card["input_schema"] = card.get("input_schema", {"type": "task-specific-features"})
        card["output_schema"] = card.get("output_schema", {"type": "capability-guidance"})
        if not isinstance(card["input_schema"], dict) or not isinstance(card["output_schema"], dict):
            raise ValueError("input_schema and output_schema must be objects")
        confidence = float(card.get("confidence", 1.0))
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be a finite number in [0,1]")
        card["confidence"] = confidence
        return card

    def _put_card(self, connection: sqlite3.Connection, card: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        card = dict(card)
        for key in ("version", "created_at", "node_id", "score", "id"):
            card.pop(key, None)
        digest = _digest(card)
        existing = connection.execute(
            "SELECT card_json FROM cf_capability_versions WHERE capability_id=? AND content_sha256=?",
            (card["capability_id"], digest),
        ).fetchone()
        if existing:
            return json.loads(existing[0]), False
        version = connection.execute(
            "SELECT COALESCE(MAX(version),0)+1 FROM cf_capability_versions WHERE capability_id=?",
            (card["capability_id"],),
        ).fetchone()[0]
        card.update(version=version, created_at=_now(), id=card["capability_id"])
        node_id = _node_id(card)
        connection.execute(
            "INSERT INTO cf_capability_versions VALUES (?,?,?,?,?,?,?)",
            (card["capability_id"], version, digest, card["status"], card["origin"],
             _json(card), card["created_at"]),
        )
        self._node(connection, node_id, "Capability", card["name"], {
            "capability_id": card["capability_id"], "version": version,
            "status": card["status"], "origin": card["origin"],
        })
        if version > 1:
            self._edge(connection, node_id, f"capability:{card['capability_id']}:v{version - 1}",
                       "SUPERSEDES", origin=card["origin"])
        for task in card["task_types"]:
            task_id = "task:" + task
            self._node(connection, task_id, "TaskType", task, {})
            self._edge(connection, node_id, task_id, "SOLVES", origin=card["origin"])
        for source in card["evidence"]:
            self._edge(connection, node_id, source["source_id"], "DERIVED_FROM",
                       locator=source["locator"], origin=card["origin"])
        for use in card["uses"]:
            use = {"kind": "Algorithm", "label": use} if isinstance(use, str) else use
            kind, label = use.get("kind", "Algorithm"), str(use["label"])
            if kind not in {"Algorithm", "Transform", "Metric"}:
                raise ValueError("Capability uses kind must be Algorithm, Transform or Metric")
            use_id = f"{kind.lower()}:{label}"
            self._node(connection, use_id, kind, label, {})
            self._edge(connection, node_id, use_id, "USES", origin=card["origin"])
        for dependency in card["dependencies"]:
            dependency = str(dependency)
            dep_id = "environment:" + dependency
            self._node(connection, dep_id, "Environment", dependency, {})
            self._edge(connection, node_id, dep_id, "REQUIRES", origin=card["origin"])
        return card, True

    def ingest_sources(self, root: Path, extractor: Callable | None = None) -> dict[str, Any]:
        """Ingest reproducible manual cards, optionally adding schema-checked LLM cards.

        ``extractor`` receives source dictionaries and returns a list of cards, or
        {"cards": [...]}. It is called outside database transactions. Generated
        claims are never promoted to verified merely because the LLM says so.
        """
        self.initialize()
        sources, issues = collect_sources(Path(root))
        by_id = {source["source_id"]: source for source in sources}
        by_key = {source["source_key"]: source for source in sources}
        seed_file = Path(root) / "knowledge/seed_capabilities.json"
        if not seed_file.exists():
            seed_file = _ASSETS / "seed_capabilities.json"
        seeds = json.loads(seed_file.read_text(encoding="utf-8"))
        pending = []
        for seed in seeds:
            seed = dict(seed)
            required = seed.pop("source_keys")
            if any(key not in by_key for key in required):
                issues.append({"capability_id": seed["capability_id"],
                               "error": "Required source unavailable; seed not ingested"})
                continue
            seed["evidence"] = [by_key[key]["source_id"] for key in required]
            seed.update(origin="manual_seed", status="extracted",
                        extraction_method="curated-source-grounded")
            pending.append(self._validate_card(seed, by_id))
        extracted_count = 0
        if extractor is not None:
            try:
                extracted = extractor(sources)
                if isinstance(extracted, dict):
                    extracted = extracted.get("cards", extracted.get("capabilities", []))
                if not isinstance(extracted, list):
                    raise ValueError("Extractor must return a list of capability cards")
                if len(extracted) > 100:
                    raise ValueError("Extractor batch exceeds 100 cards")
                for index, item in enumerate(extracted):
                    try:
                        candidate = dict(item)
                        candidate_id = candidate.get("capability_id", candidate.get("id"))
                        if any(c["capability_id"] == candidate_id and c["origin"] == "manual_seed"
                               for c in pending):
                            raise ValueError("LLM extraction cannot replace a manual seed identity")
                        candidate.update(origin="llm_extracted", status="extracted",
                                         extraction_method="llm-with-source-validation")
                        pending.append(self._validate_card(candidate, by_id))
                        extracted_count += 1
                    except (ValueError, TypeError, KeyError, AttributeError) as exc:
                        issues.append({"extracted_index": index, "error": str(exc)})
            except Exception as exc:
                issues.append({"stage": "llm_extraction", "error_type": type(exc).__name__,
                               "error": str(exc)})
        created = 0
        with self._connection(write=True) as connection:
            for source in sources:
                self._source(connection, source)
            saved = []
            for card in pending:
                result, inserted = self._put_card(connection, card)
                created += int(inserted)
                saved.append(result)
            latest = {card["capability_id"]: card for card in self._latest(connection)}
            for card in saved:
                for related in card["related"]:
                    if related in latest:
                        self._edge(connection, _node_id(card), _node_id(latest[related]),
                                   "REQUIRES", origin=card["origin"], reason="curated dependency")
        return {"sources": len(sources), "manual_seed_cards": len(pending) - extracted_count,
                "llm_extracted_cards": extracted_count, "new_capability_versions": created,
                "total_capabilities": len(self.list_capabilities()), "issues": issues,
                "source_manifest": [{key: value for key, value in source.items() if key != "content"}
                                    for source in sources],
                "extraction_performed": extractor is not None}

    @staticmethod
    def _latest(connection: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = connection.execute(
            "SELECT c.card_json FROM cf_capability_versions c JOIN "
            "(SELECT capability_id,MAX(version) version FROM cf_capability_versions GROUP BY capability_id) m "
            "ON c.capability_id=m.capability_id AND c.version=m.version ORDER BY c.capability_id",
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def list_capabilities(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            return self._latest(connection)

    def search(self, query: str, task_type: str, limit: int = 6,
               use_graph: bool = True) -> list[dict[str, Any]]:
        if task_type not in TASK_TYPES:
            raise ValueError(f"Unsupported task type: {task_type}")
        if limit <= 0:
            return []
        with self._connection() as connection:
            cards = [c for c in self._latest(connection)
                     if task_type in c["task_types"] and c["status"] in {"extracted", "verified"}]
            graph_rows = connection.execute("SELECT source_id,target_id,relation FROM cf_edges").fetchall()
        query_tokens = _tokens(query)
        scores, paths = {}, {}
        for card in cards:
            title = _tokens(card["name"] + " " + " ".join(map(str, card["tags"])))
            body = _tokens(card["summary"] + " " + " ".join(map(str, card["preconditions"])))
            lexical = (2 * len(query_tokens & title) + len(query_tokens & body))
            lexical /= max(1.0, math.sqrt(len(query_tokens)))
            scores[_node_id(card)] = lexical
            paths[_node_id(card)] = []
        base_scores = dict(scores)
        if use_graph and query_tokens:
            adjacency: dict[str, list[tuple[str, str]]] = {}
            for source, target, relation in graph_rows:
                if relation not in {"USES", "REQUIRES", "AVOIDED_BY"}:
                    continue
                # A ubiquitous Python/sklearn dependency is not evidence of task similarity.
                if source.startswith("environment:") or target.startswith("environment:"):
                    continue
                adjacency.setdefault(source, []).append((target, relation))
                adjacency.setdefault(target, []).append((source, relation))
            seeds = sorted(scores, key=lambda key: (-scores[key], key))[:3]
            for seed in seeds:
                if base_scores[seed] <= 0:
                    continue
                queue = deque([(seed, [])])
                seen = {seed}
                while queue:
                    current, path = queue.popleft()
                    if len(path) >= 2:
                        continue
                    for neighbor, relation in adjacency.get(current, []):
                        if neighbor in seen:
                            continue
                        seen.add(neighbor)
                        next_path = path + [{"from": current, "relation": relation, "to": neighbor}]
                        queue.append((neighbor, next_path))
                        if neighbor in scores and neighbor != seed:
                            bonus = min(base_scores[seed], 3.0) * 0.4 / len(next_path)
                            scores[neighbor] += bonus
                            paths[neighbor].append({"seed": seed, "hops": next_path, "bonus": bonus})
        results = []
        for card in sorted(cards, key=lambda c: (-scores[_node_id(c)], c["capability_id"]))[:min(limit, 50)]:
            node_id = _node_id(card)
            card.update(score=round(scores[node_id], 6), lexical_score=round(base_scores[node_id], 6),
                        graph_score=round(scores[node_id] - base_scores[node_id], 6),
                        evidence_path=paths[node_id], graph_used=use_graph,
                        source_locator=[e["locator"] for e in card["evidence"]],
                        matched_constraints=[f"task_type={task_type}"],
                        rejected_reason=None)
            results.append(card)
        return results

    def _ensure_run(self, connection: sqlite3.Connection, run_id: str) -> None:
        if not run_id:
            raise ValueError("run_id is required")
        now = _now()
        connection.execute(
            "INSERT OR IGNORE INTO cf_runs VALUES (?,?,?,?,?)",
            (run_id, "running", _json({"run_id": run_id, "status": "running"}), now, now),
        )
        present = connection.execute("SELECT status FROM cf_runs WHERE run_id=?", (run_id,)).fetchone()
        self._node(connection, "run:" + run_id, "ValidationRun", run_id, {"status": present[0]})

    def add_event(self, run_id: str, event: dict[str, Any]) -> None:
        with self._connection(write=True) as connection:
            self._ensure_run(connection, run_id)
            event = dict(event)
            event_id = str(event.get("event_id") or "event-" + uuid.uuid4().hex)
            existing = connection.execute("SELECT run_id FROM cf_events WHERE event_id=?", (event_id,)).fetchone()
            if existing and existing[0] != run_id:
                raise ValueError("event_id already belongs to another run")
            if existing:
                return
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence),0)+1 FROM cf_events WHERE run_id=?", (run_id,),
            ).fetchone()[0]
            event.update(event_id=event_id, sequence=sequence)
            event_type = str(event.get("event_type", event.get("type", event.get("stage", "event"))))
            connection.execute("INSERT INTO cf_events VALUES (?,?,?,?,?,?)",
                               (event_id, run_id, sequence, event_type, _json(event), _now()))

    def save_run(self, report: dict[str, Any]) -> None:
        report = dict(report)
        run_id = str(report.get("run_id", report.get("id", "")))
        if not run_id:
            raise ValueError("Run report requires run_id")
        report["run_id"] = run_id
        status = str(report.get("status", "unknown"))
        with self._connection(write=True) as connection:
            self._ensure_run(connection, run_id)
            now, digest = _now(), _digest(report)
            connection.execute(
                "UPDATE cf_runs SET status=?, report_json=?, updated_at=? WHERE run_id=?",
                (status, _json(report), now, run_id),
            )
            revision = connection.execute(
                "SELECT COALESCE(MAX(revision),0)+1 FROM cf_run_revisions WHERE run_id=?", (run_id,),
            ).fetchone()[0]
            connection.execute(
                "INSERT OR IGNORE INTO cf_run_revisions VALUES (?,?,?,?,?)",
                (run_id, revision, digest, _json(report), now),
            )
            self._node(connection, "run:" + run_id, "ValidationRun", run_id,
                       {"status": status, "mode": report.get("mode", "unspecified"), "run_id": run_id})
            task = report.get("task_spec", report.get("task", {}))
            task = task if isinstance(task, dict) else {}
            dataset = task.get("dataset_version", task.get("dataset_id", report.get("dataset_id")))
            if dataset:
                dataset = str(dataset)
                self._node(connection, "dataset:" + dataset, "DatasetVersion", dataset, {
                    "split_id": task.get("split_id"), "feature_policy": task.get("feature_policy"),
                })
                self._edge(connection, "run:" + run_id, "dataset:" + dataset, "EVALUATED_ON")
            metrics = report.get("metrics", {})
            if isinstance(metrics, dict):
                for metric, value in metrics.items():
                    self._node(connection, "metric:" + metric, "Metric", metric, {})
                    self._edge(connection, "run:" + run_id, "metric:" + metric,
                               "MEASURED_BY", value=value)
            artifacts = report.get("artifacts", [])
            if isinstance(artifacts, dict):
                artifacts = [{"path": value, "name": key} for key, value in artifacts.items()]
            if not isinstance(artifacts, list):
                artifacts = []
            else:
                artifacts = list(artifacts)
            for candidate in report.get("candidates", []):
                if isinstance(candidate, dict) and candidate.get("artifact"):
                    artifacts.append(candidate["artifact"])
                if not isinstance(candidate, dict):
                    continue
                previous_artifact = None
                for attempt in candidate.get("attempts", []):
                    if not isinstance(attempt, dict) or not attempt.get("code_sha256"):
                        continue
                    identity = [run_id, candidate.get("candidate_id"), attempt.get("attempt"),
                                attempt["code_sha256"]]
                    artifact_id = "artifact-" + _digest(identity)[:24]
                    artifacts.append({
                        "artifact_id": artifact_id, "candidate_id": candidate.get("candidate_id"),
                        "path": attempt.get("code_path"), "sha256": attempt["code_sha256"],
                        "attempt": attempt.get("attempt"), "status": attempt.get("status"),
                        "metrics": attempt.get("metrics", {}), "error": attempt.get("error"),
                        "checks": attempt.get("checks", []),
                        "parent_artifact_id": previous_artifact,
                        "capability_ids": candidate.get("plan", {}).get("evidence_ids", []),
                    })
                    previous_artifact = artifact_id
            latest = {card["capability_id"]: card for card in self._latest(connection)}
            for artifact in artifacts:
                artifact = {"path": artifact} if isinstance(artifact, str) else dict(artifact)
                artifact_id = str(artifact.get("artifact_id") or "artifact-" + _digest([run_id, artifact])[:24])
                existing = connection.execute(
                    "SELECT artifact_json FROM cf_artifacts WHERE artifact_id=?", (artifact_id,),
                ).fetchone()
                if existing and _digest(json.loads(existing[0])) != _digest(artifact):
                    # Preserve original evidence when an external caller reuses an ID.
                    artifact_id += "-" + _digest(artifact)[:12]
                connection.execute(
                    "INSERT OR IGNORE INTO cf_artifacts VALUES (?,?,?,?,?)",
                    (artifact_id, run_id, artifact.get("sha256", artifact.get("source_hash")),
                     _json(artifact), now),
                )
                self._node(connection, "artifact:" + artifact_id, "Artifact",
                           str(artifact.get("path", artifact_id)), artifact)
                self._edge(connection, "run:" + run_id, "artifact:" + artifact_id, "EVALUATES")
                parent = artifact.get("parent_artifact_id")
                if parent and connection.execute(
                    "SELECT 1 FROM cf_nodes WHERE node_id=?", ("artifact:" + str(parent),),
                ).fetchone():
                    self._edge(connection, "artifact:" + artifact_id, "artifact:" + str(parent),
                               "REPAIRS", status=artifact.get("status"))
                for capability_id in artifact.get("capability_ids", []):
                    if capability_id in latest:
                        self._edge(connection, "artifact:" + artifact_id,
                                   _node_id(latest[capability_id]), "IMPLEMENTS",
                                   evidence="planner citation", validated=artifact.get("status") == "passed")

    def record_experience(self, run_id: str, error_type: str, diagnosis: str, fix: str,
                          task_type: str, validated: bool) -> dict[str, Any]:
        if task_type not in TASK_TYPES:
            raise ValueError("Unsupported experience task type")
        fingerprint = _digest([error_type, diagnosis.strip(), fix.strip(), task_type])
        failure_id = "failure-" + _digest([run_id, fingerprint, bool(validated)])[:24]
        experience = {
            "failure_id": failure_id, "fingerprint": fingerprint, "run_id": run_id,
            "error_type": error_type, "diagnosis": diagnosis, "fix": fix, "task_type": task_type,
            "validated": bool(validated), "status": "validated" if validated else "proposed",
            "origin": "runtime_experience",
        }
        with self._connection(write=True) as connection:
            self._ensure_run(connection, run_id)
            row = connection.execute("SELECT report_json,status FROM cf_runs WHERE run_id=?", (run_id,)).fetchone()
            report = json.loads(row[0])
            successful_repair = any(
                candidate.get("status") == "passed" and any(
                    repair.get("error_type") == error_type and repair.get("diagnosis") == diagnosis
                    and repair.get("fix") == fix for repair in candidate.get("repairs", [])
                ) for candidate in report.get("candidates", []) if isinstance(candidate, dict)
            )
            if validated and row[1] not in {"passed", "completed", "succeeded", "success"} and not successful_repair:
                raise ValueError("Validated experience requires a persisted successful validation run")
            connection.execute("INSERT OR IGNORE INTO cf_failures VALUES (?,?,?,?,?,?,?)",
                               (failure_id, fingerprint, run_id, task_type, int(bool(validated)),
                                _json(experience), _now()))
            self._node(connection, failure_id, "FailureExperience", error_type, experience)
            self._edge(connection, failure_id, "run:" + run_id, "DERIVED_FROM",
                       status=experience["status"])
            if validated:
                source = {
                    "source_id": "src-run-" + _digest([run_id, report])[:24],
                    "source_key": "validation:" + run_id, "uri": f"run://{run_id}",
                    "revision": _digest(report), "license": "original-runtime-evidence",
                    "content_sha256": _digest(report), "content": _json(experience),
                    "locator": {"run_id": run_id, "failure_id": failure_id}, "kind": "validation_run",
                }
                self._source(connection, source)
                card = self._validate_card({
                    "capability_id": "repair-" + fingerprint[:20],
                    "name": f"Validated repair: {error_type}",
                    "summary": diagnosis + "\nValidated fix: " + fix,
                    "task_types": [task_type], "evidence": [source["source_id"]],
                    "origin": "runtime_experience", "status": "verified",
                    "preconditions": [diagnosis], "tags": [error_type, "validated repair"],
                    "validation_runs": [run_id],
                }, {source["source_id"]: source})
                saved, _ = self._put_card(connection, card)
                self._edge(connection, failure_id, _node_id(saved), "AVOIDED_BY", validated=True)
                self._edge(connection, _node_id(saved), "run:" + run_id, "DERIVED_FROM")
        return experience

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT report_json FROM cf_runs WHERE run_id=?", (run_id,)).fetchone()
            if row is None:
                return None
            report = json.loads(row[0])
            stored_events = [json.loads(row[0]) for row in connection.execute(
                "SELECT event_json FROM cf_events WHERE run_id=? ORDER BY sequence", (run_id,),
            )]
            report["events"] = stored_events or report.get("events", [])
            report["experiences"] = [json.loads(row[0]) for row in connection.execute(
                "SELECT experience_json FROM cf_failures WHERE run_id=? ORDER BY created_at", (run_id,),
            )]
            report["revision_count"] = connection.execute(
                "SELECT COUNT(*) FROM cf_run_revisions WHERE run_id=?", (run_id,),
            ).fetchone()[0]
            return report

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        with self._connection() as connection:
            return [json.loads(row[0]) for row in connection.execute(
                "SELECT report_json FROM cf_runs ORDER BY updated_at DESC LIMIT ?", (min(limit, 1000),),
            )]

    def graph(self) -> dict[str, Any]:
        with self._connection() as connection:
            nodes = [{"id": row[0], "kind": row[1], "label": row[2],
                      "properties": json.loads(row[3])}
                     for row in connection.execute("SELECT * FROM cf_nodes ORDER BY node_id")]
            edges = [{"id": row[0], "source": row[1], "target": row[2],
                      "relation": row[3], "properties": json.loads(row[4])}
                     for row in connection.execute("SELECT * FROM cf_edges ORDER BY edge_id")]
        return {"nodes": nodes, "edges": edges}
