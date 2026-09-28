"""Extraction metrics must separate schemas, provenance, and unmeasured semantics."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("evaluate_extraction", ROOT / "scripts/evaluate_extraction.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.fixture
def sample(tmp_path):
    locator = {"path": str(tmp_path / "docs/public.md"), "line_start": 1, "line_end": 3}
    source = {"source_id": "src-public", "source_key": "public-note", "uri": "file:///root/docs/public.md",
              "revision": "sha256:example", "content_sha256": "a" * 64, "license": "project-notes",
              "locator": locator, "content": "Public source explains Pipeline."}
    card = {"capability_id": "pipeline", "name": "Pipeline", "summary": "Compose transformations.",
            "task_types": ["tabular_binary_classification"], "inputs": ["features"],
            "outputs": ["predictions"], "preconditions": ["fit on training data"],
            "dependencies": ["scikit-learn"], "source_ids": ["src-public"], "metrics": []}
    artifact = {"mode": "real", "model": "test-recorded-model", "sources": [copy.deepcopy(source)],
                "summary": {"source_manifest": [copy.deepcopy(source)]}, "result": {"capabilities": [card]},
                "usage": {"calls": 1, "input_tokens": 100, "output_tokens": 20, "cached_input_tokens": 0}}
    gold = {"annotation_origin": "explicit project references", "assertions": [
        {"subject": "Pipeline", "predicate": "kind", "object": "class", "source_key": "public-note"},
        {"subject": "Unseen", "predicate": "kind", "object": "class", "source_key": "unsent-source"},
    ]}
    return artifact, gold, [source], tmp_path


def test_structural_metrics_do_not_become_semantic_precision(sample):
    artifact, gold, trusted, root = sample
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    assert report["structural_quality"]["valid_card_rate"] == 1
    assert report["provenance"]["reference_resolution_rate"] == 1
    assert report["provenance"]["verified_submitted_excerpts"] == 1
    assert report["semantic_precision"] is None
    assert report["semantic_recall"] is None
    assert report["new_model_calls"] == 0
    assert report["gold_assertion_evaluation"]["precision"] is None
    assert report["gold_assertion_evaluation"]["reference_assertions_in_submitted_source_scope"] == 1


def test_unknown_source_and_modified_excerpt_are_visible(sample):
    artifact, gold, trusted, root = sample
    artifact["result"]["capabilities"][0]["source_ids"].append("fabricated-source")
    artifact["sources"][0]["content"] = "Modified evidence"
    artifact["sources"][0]["locator"]["path"] = "/root/.env"
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    assert report["provenance"]["reference_resolution_rate"] == 0.5
    assert report["provenance"]["verified_submitted_excerpts"] == 0
    assert report["provenance"]["verified_source_locators"] == 0
    assert report["card_checks"][0]["unresolved_source_ids"] == ["fabricated-source"]


def test_empty_fields_and_exact_duplicates_are_counted(sample):
    artifact, gold, trusted, root = sample
    second = copy.deepcopy(artifact["result"]["capabilities"][0])
    second["outputs"] = []
    artifact["result"]["capabilities"].append(second)
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    quality = report["structural_quality"]
    assert quality["valid_card_rate"] == 0.5
    assert quality["duplicate_id_count"] == 1
    assert quality["duplicate_id_rate"] == 0.5
    assert quality["exact_duplicate_summary_count"] == 1
    assert quality["semantic_duplicate_rate"] is None


def test_empty_record_has_undefined_rates(sample):
    artifact, gold, trusted, root = sample
    artifact["result"]["capabilities"] = []
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    assert report["structural_quality"]["valid_card_rate"] is None
    assert report["provenance"]["reference_resolution_rate"] is None


def test_invalid_card_shapes_do_not_crash(sample):
    artifact, gold, trusted, root = sample
    artifact["result"]["capabilities"][0]["task_types"] = [{"unsupported": "object"}]
    artifact["result"]["capabilities"].append("not-a-card")
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    assert report["structural_quality"]["valid_card_rate"] == 0


def test_method_mislabeled_as_metric_is_flagged(sample):
    artifact, gold, trusted, root = sample
    artifact["result"]["capabilities"][0]["metrics"] = ["predict_proba", "score"]
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    assert len(report["automatic_review_flags"]["method_names_used_as_metrics"]) == 1
    assert len(report["automatic_review_flags"]["ambiguous_score_metric_labels"]) == 1


def test_exact_assertion_agreement_is_computed_only_with_compatible_output(sample):
    artifact, gold, trusted, root = sample
    artifact["result"]["assertions"] = [gold["assertions"][0]]
    report = MODULE.evaluate_recorded_extraction(artifact, gold, root, trusted)
    result = report["gold_assertion_evaluation"]
    assert result["status"] == "evaluated_exact_assertion_agreement"
    assert result["precision"] == 1
    assert result["recall"] == 1
    assert result["reference_assertions_outside_submitted_source_scope"] == 1
    assert report["semantic_precision"] is None


def test_public_export_allowlist_removes_secrets_paths_and_raw_logs(sample):
    artifact, _, trusted, root = sample
    synthetic_secret = "sk-" + "test" * 8
    artifact["private_context"] = {"Authorization": synthetic_secret}
    artifact["usage"]["records"] = [{"prompt": synthetic_secret, "path": "/root/.env"}]
    artifact["result"]["capabilities"][0]["debug"] = synthetic_secret
    artifact["result"]["capabilities"][0]["summary"] += " Debug /root/private/token.txt " + synthetic_secret
    public = MODULE.export_public_evidence(artifact, root, trusted)
    payload = json.dumps(public)
    assert synthetic_secret not in payload
    assert "/root/" not in payload
    assert str(root) not in payload
    assert "Authorization" not in payload
    assert "private_context" not in payload
    assert "records" not in public["usage"]
    assert public["usage"]["calls"] == 1
    assert "content" not in public["sources"][0]
    assert public["sources"][0]["locator"]["relative_path"] == "docs/public.md"


def test_committed_public_evidence_is_small_and_contains_only_public_payload():
    path = ROOT / "examples/evidence/knowledge_extraction.json"
    public = json.loads(path.read_text(encoding="utf-8"))
    assert public["mode"] == "real"
    assert len(public["capabilities"]) == 9
    assert len(public["sources"]) == 10
    assert public["usage"]["calls"] == 1
    assert path.stat().st_size < 30000
    text = path.read_text(encoding="utf-8")
    assert "/root/" not in text
    assert "Authorization" not in text
    assert all("path" not in source["locator"] for source in public["sources"])
