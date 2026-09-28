"""Knowledge provenance, immutable history, graph use, and concurrency contracts."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from capability_factory.ingestion import TABULAR, TEXT, parse_python_source, read_document
from capability_factory.knowledge import KnowledgeStore

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def store(tmp_path):
    result = KnowledgeStore(tmp_path / "knowledge.sqlite")
    result.initialize()
    return result


@pytest.fixture
def ingested(store):
    result = store.ingest_sources(ROOT)
    assert result["issues"] == []
    return store


def test_real_corpus_has_verified_locators_and_distinct_origins(ingested):
    cards = ingested.list_capabilities()
    assert len(cards) >= 12
    assert {card["origin"] for card in cards} == {"manual_seed"}
    assert {card["status"] for card in cards} == {"extracted"}
    for card in cards:
        for evidence in card["evidence"]:
            path = Path(evidence["locator"]["path"])
            assert path.exists()
            assert evidence["content_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert 1 <= evidence["locator"]["line_start"] <= evidence["locator"]["line_end"]
            assert evidence["locator"]["line_end"] <= len(path.read_bytes().splitlines())


def test_ingestion_is_idempotent_and_leaves_no_orphan_edges(ingested):
    first = ingested.graph()
    second = ingested.ingest_sources(ROOT)
    assert second["new_capability_versions"] == 0
    assert ingested.graph() == first
    ids = {node["id"] for node in first["nodes"]}
    assert all(edge["source"] in ids and edge["target"] in ids for edge in first["edges"])


def test_graph_paths_actually_change_ranking_scores(ingested):
    plain = {c["id"]: c for c in ingested.search("未知类别 OneHotEncoder", TABULAR, 50, False)}
    graph = {c["id"]: c for c in ingested.search("未知类别 OneHotEncoder", TABULAR, 50, True)}
    assert graph["mixed-type-columns"]["score"] > plain["mixed-type-columns"]["score"]
    assert graph["mixed-type-columns"]["evidence_path"]
    assert all(c["graph_score"] == 0 for c in plain.values())
    assert any(c["graph_score"] > 0 for c in graph.values())


def test_task_filter_prevents_cross_domain_suggestions(ingested):
    text_cards = ingested.search("短信 TF-IDF", TEXT, 50)
    assert "bank-precontact-policy" not in {c["id"] for c in text_cards}
    assert all(TEXT in c["task_types"] for c in text_cards)
    assert ingested.search("anything", TEXT, limit=0) == []
    with pytest.raises(ValueError, match="Unsupported"):
        ingested.search("anything", "unknown-task")


def test_ast_ingestion_never_executes_source(tmp_path):
    marker = tmp_path / "should-not-exist"
    source = tmp_path / "untrusted.py"
    source.write_text(
        f"open({str(marker)!r}, 'w').write('executed')\n"
        "import os\nclass Example:\n    '''Source documentation.'''\n"
        "    def __init__(self, amount=2):\n        self.amount = amount\n"
    )
    result = parse_python_source(source, key="example", symbol="Example")
    assert not marker.exists()
    assert result["locator"]["line_start"] == 3
    assert "import os" in result["locator"]["imports"]
    assert "amount=2" in result["locator"]["signature"]
    assert result["locator"]["parse_mode"] == "ast-only"


def test_document_marker_is_required(tmp_path):
    path = tmp_path / "source.md"
    path.write_text("# Overview\nOnly real material\n")
    with pytest.raises(ValueError, match="absent"):
        read_document(path, key="overview", marker="fictional section")


def test_llm_extraction_requires_real_sources_and_never_self_verifies(store):
    def extractor(sources):
        valid = {
            "capability_id": "generated-pipeline",
            "name": "Extracted pipeline",
            "summary": "Pipeline combines transformations and an estimator.",
            "task_types": [TABULAR],
            "source_ids": [next(s["source_id"] for s in sources if s["source_key"] == "sklearn-pipeline")],
            "status": "verified",
            "origin": "manual_seed",
        }
        return [valid, dict(valid, capability_id="fabricated-source", source_ids=["missing-source"])]
    result = store.ingest_sources(ROOT, extractor)
    assert result["llm_extracted_cards"] == 1
    assert any("Unknown evidence source" in issue["error"] for issue in result["issues"])
    card = next(card for card in store.list_capabilities() if card["id"] == "generated-pipeline")
    assert card["origin"] == "llm_extracted"
    assert card["status"] == "extracted"
    assert "fabricated-source" not in {card["id"] for card in store.list_capabilities()}


def test_extractor_failure_is_reported_not_labeled_as_success(store):
    def broken(_):
        raise TimeoutError("external extractor timed out")
    summary = store.ingest_sources(ROOT, broken)
    assert summary["llm_extracted_cards"] == 0
    assert summary["manual_seed_cards"] >= 12
    assert summary["issues"][-1]["error_type"] == "TimeoutError"


def test_capability_versions_are_immutable_and_linked(store):
    def extracted(summary):
        def generate(sources):
            return [{"capability_id": "versioned-card", "name": "Version test", "summary": summary,
                     "task_types": [TABULAR], "source_ids": [sources[0]["source_id"]]}]
        return generate
    store.ingest_sources(ROOT, extracted("First source-backed description"))
    store.ingest_sources(ROOT, extracted("Updated source-backed description"))
    card = next(c for c in store.list_capabilities() if c["id"] == "versioned-card")
    assert card["version"] == 2
    assert any(e["relation"] == "SUPERSEDES" and e["source"] == "capability:versioned-card:v2"
               for e in store.graph()["edges"])
    with sqlite3.connect(store.db_path) as connection:
        old = connection.execute("SELECT card_json FROM cf_capability_versions WHERE capability_id=? AND version=1",
                                 ("versioned-card",)).fetchone()
    assert json.loads(old[0])["summary"] == "First source-backed description"


def test_failed_runs_and_updated_reports_preserve_history(store):
    store.save_run({"run_id": "failed-run", "status": "failed", "error": "InvalidProbability"})
    assert store.get_run("failed-run")["status"] == "failed"
    assert store.list_runs()[0]["error"] == "InvalidProbability"
    store.save_run({"run_id": "failed-run", "status": "passed", "metrics": {"average_precision": 0.4}})
    store.save_run({"run_id": "failed-run", "status": "passed", "metrics": {"average_precision": 0.4}})
    assert store.get_run("failed-run")["revision_count"] == 2
    with sqlite3.connect(store.db_path) as connection:
        original = connection.execute("SELECT report_json FROM cf_run_revisions WHERE run_id=? AND revision=1",
                                      ("failed-run",)).fetchone()
    assert json.loads(original[0])["status"] == "failed"
    assert store.get_run("missing") is None


def test_concurrent_events_have_unique_contiguous_sequence(store):
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda i: store.add_event("concurrent", {"type": "progress", "i": i}), range(32)))
    events = store.get_run("concurrent")["events"]
    assert [e["sequence"] for e in events] == list(range(1, 33))
    assert len({e["i"] for e in events}) == 32
    store.add_event("concurrent", {"event_id": "same-id", "type": "completed"})
    store.add_event("concurrent", {"event_id": "same-id", "type": "completed"})
    assert len(store.get_run("concurrent")["events"]) == 33


def test_unvalidated_failure_is_kept_but_not_trusted_for_retrieval(ingested):
    before = len(ingested.list_capabilities())
    item = ingested.record_experience("r-failed", "NegativeInput", "Negative sparse features",
                                      "Do not center TF-IDF", TEXT, False)
    assert item["status"] == "proposed"
    assert len(ingested.list_capabilities()) == before
    assert ingested.get_run("r-failed")["experiences"][0]["validated"] is False
    with pytest.raises(ValueError, match="successful validation"):
        ingested.record_experience("r-failed", "NegativeInput", "Negative sparse features",
                                   "Do not center TF-IDF", TEXT, True)


def test_validated_repair_has_run_provenance_and_is_retrievable(ingested):
    ingested.save_run({"run_id": "repair-ok", "status": "passed", "metrics": {"average_precision": 0.9}})
    experience = ingested.record_experience("repair-ok", "NegativeInput", "Negative sparse features",
                                           "Keep TF-IDF nonnegative; set with_mean=False", TEXT, True)
    ingested.record_experience("repair-ok", "NegativeInput", "Negative sparse features",
                              "Keep TF-IDF nonnegative; set with_mean=False", TEXT, True)
    repair = next(c for c in ingested.list_capabilities() if c["origin"] == "runtime_experience")
    assert repair["status"] == "verified"
    assert repair["version"] == 1
    assert repair["validation_runs"] == ["repair-ok"]
    assert repair["evidence"][0]["locator"]["run_id"] == "repair-ok"
    assert repair["id"] in {c["id"] for c in ingested.search("NegativeInput nonnegative", TEXT)}
    assert any(e["source"] == experience["failure_id"] and e["relation"] == "AVOIDED_BY"
               for e in ingested.graph()["edges"])


def test_run_artifact_and_dataset_relations(store):
    store.save_run({
        "run_id": "lineage", "status": "passed", "mode": "real",
        "task_spec": {"dataset_id": "bank-v1", "split_id": "ordered-v1"},
        "metrics": {"average_precision": 0.2},
        "artifacts": [{"artifact_id": "code1", "path": "runs/lineage/model.py", "sha256": "a" * 64}],
    })
    relations = {e["relation"] for e in store.graph()["edges"]}
    assert {"EVALUATED_ON", "MEASURED_BY", "EVALUATES"} <= relations


def test_in_memory_database_and_repeated_initialize():
    store = KnowledgeStore(":memory:")
    store.initialize()
    store.save_run({"run_id": "memory", "status": "failed"})
    store.initialize()
    assert store.get_run("memory")["status"] == "failed"
    store.close()


def test_malformed_llm_relations_do_not_rollback_manual_corpus(store):
    def extractor(sources):
        return [{"capability_id": "bad-use", "name": "Bad use", "summary": "Unsupported relation",
                 "task_types": [TABULAR], "source_ids": [sources[0]["source_id"]],
                 "uses": [{"kind": "ExecuteShell", "label": "untrusted"}]}]
    result = store.ingest_sources(ROOT, extractor)
    assert result["manual_seed_cards"] >= 12
    assert result["llm_extracted_cards"] == 0
    assert "uses kind" in result["issues"][0]["error"]
    assert len(store.list_capabilities()) >= 12


def test_llm_cannot_replace_curated_seed_identity(store):
    def extractor(sources):
        return [{"capability_id": "bank-precontact-policy", "name": "Unsafe overwrite",
                 "summary": "Use all columns including duration", "task_types": [TABULAR],
                 "source_ids": [sources[0]["source_id"]]}]
    result = store.ingest_sources(ROOT, extractor)
    assert result["llm_extracted_cards"] == 0
    card = next(c for c in store.list_capabilities() if c["id"] == "bank-precontact-policy")
    assert card["origin"] == "manual_seed"
    assert "禁止使用 duration" in card["summary"]


def test_attempt_artifacts_form_repair_and_capability_lineage(ingested):
    report = {"run_id": "attempt-lineage", "status": "passed", "candidates": [{
        "candidate_id": "linear", "plan": {"evidence_ids": ["probability-logistic"]},
        "attempts": [
            {"attempt": 0, "code_sha256": "a" * 64, "code_path": "attempt_0/model.py",
             "status": "failed", "error": {"type": "MissingInterface"}},
            {"attempt": 1, "code_sha256": "b" * 64, "code_path": "attempt_1/model.py", "status": "passed"},
        ],
    }]}
    ingested.save_run(report)
    ingested.save_run(report)
    graph = ingested.graph()
    artifacts = [node for node in graph["nodes"] if node["kind"] == "Artifact"]
    assert len(artifacts) == 2
    assert {node["properties"]["status"] for node in artifacts} == {"passed", "failed"}
    assert sum(edge["relation"] == "REPAIRS" for edge in graph["edges"]) == 1
    assert sum(edge["relation"] == "IMPLEMENTS" for edge in graph["edges"]) == 2


def test_validated_candidate_survives_aggregate_orchestration_failure(store):
    repair = {"error_type": "MissingInterface", "diagnosis": "builder absent", "fix": "add builder"}
    store.save_run({"run_id": "partly-failed", "status": "failed", "candidates": [
        {"status": "passed", "repairs": [repair]}, {"status": "failed", "repairs": []},
    ]})
    result = store.record_experience("partly-failed", **repair, task_type=TABULAR, validated=True)
    assert result["validated"] is True
    assert store.get_run("partly-failed")["status"] == "failed"


def test_extraction_agreement_does_not_treat_missing_output_as_perfect():
    from capability_factory.ingestion import evaluate_assertions
    reference = [{"subject": "Pipeline", "predicate": "kind", "object": "class", "source_key": "sklearn-pipeline"}]
    empty = evaluate_assertions([], reference)
    assert empty["precision"] is None
    assert empty["recall"] == 0
    predictions = reference + [{"subject": "Pipeline", "predicate": "kind", "object": "function", "source_key": "unknown"}]
    score = evaluate_assertions(predictions, reference, {"sklearn-pipeline"})
    assert score["precision"] == 0.5
    assert score["recall"] == 1
    assert score["source_key_valid_rate"] == 0.5
    assert len(score["false_positives"]) == 1


def test_gold_assertions_have_existing_source_keys(store):
    summary = store.ingest_sources(ROOT)
    keys = {source["source_key"] for source in summary["source_manifest"]}
    gold = json.loads((ROOT / "knowledge/extraction_gold.json").read_text())["assertions"]
    assert len(gold) >= 30
    assert all(item["source_key"] in keys for item in gold)
