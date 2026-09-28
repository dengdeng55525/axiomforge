"""Recheck recorded extraction locally and export a small sanitized public artifact.

No LLM calls or environment configuration are used. Structural validity, verifiable
source provenance, and semantic agreement are deliberately separate quantities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from capability_factory.ingestion import collect_sources, evaluate_assertions

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = (
    "capability_id", "name", "summary", "task_types", "inputs", "outputs",
    "preconditions", "dependencies", "source_ids",
)
CARD_FIELDS = (*REQUIRED_FIELDS, "metrics", "confidence", "tags")
USAGE_FIELDS = ("calls", "input_tokens", "output_tokens", "cached_input_tokens")
ALLOWED_TASKS = {"tabular_binary_classification", "text_binary_classification"}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(isinstance(item, str) and bool(item.strip()) for item in value)
    return False


def _cards(artifact: dict[str, Any]) -> list[Any]:
    result = artifact.get("result", {})
    cards = result.get("capabilities", result.get("cards", [])) if isinstance(result, dict) else []
    return cards if isinstance(cards, list) else []


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _duplicate_count(values: list[str]) -> int:
    return sum(count - 1 for count in Counter(_normalize(value) for value in values).values())


def evaluate_recorded_extraction(artifact: dict[str, Any], gold: dict[str, Any], root: Path,
                                 trusted_sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Validate only approved source files, never paths supplied by a model/card."""
    issues = []
    if trusted_sources is None:
        trusted_sources, issues = collect_sources(root)
    trusted = {source["source_id"]: source for source in trusted_sources}
    submitted = artifact.get("sources", [])
    submitted = [source for source in submitted if isinstance(source, dict)]
    submitted_by_id = {source.get("source_id"): source for source in submitted}
    manifest = artifact.get("summary", {}).get("source_manifest", [])
    manifest = {source.get("source_id"): source for source in manifest if isinstance(source, dict)}
    source_checks = []
    for source in submitted:
        source_id = source.get("source_id")
        current = trusted.get(source_id)
        recorded = manifest.get(source_id, {})
        locator = source.get("locator", {})
        expected_locator = current.get("locator", {}) if current else {}
        # Reading is performed only by collect_sources' fixed allowlist, never by locator.path.
        locator_matches = bool(current) and all(
            locator.get(key) == expected_locator.get(key)
            for key in ("path", "line_start", "line_end", "symbol")
        )
        source_checks.append({
            "source_id": source_id, "source_key": source.get("source_key"),
            "known_current_source": bool(current), "locator_matches": locator_matches,
            "file_sha256_matches": bool(current and recorded.get("content_sha256")
                                        and recorded["content_sha256"] == current.get("content_sha256")),
            "submitted_excerpt_matches": bool(current and isinstance(source.get("content"), str)
                                              and source["content"] == current.get("content")),
        })
    raw_cards = _cards(artifact)
    cards = [card for card in raw_cards if isinstance(card, dict)]
    total = len(raw_cards)
    checks = []
    refs_total, refs_resolved = 0, 0
    for index, card in enumerate(raw_cards):
        if not isinstance(card, dict):
            checks.append({"index": index, "schema_valid": False, "error": "card is not an object"})
            continue
        missing = [field for field in REQUIRED_FIELDS if not _nonempty(card.get(field))]
        wrong_types = []
        for field in ("capability_id", "name", "summary"):
            if not isinstance(card.get(field), str):
                wrong_types.append(field)
        for field in ("task_types", "inputs", "outputs", "preconditions", "dependencies", "source_ids"):
            if not isinstance(card.get(field), list):
                wrong_types.append(field)
        tasks = card.get("task_types", [])
        task_valid = isinstance(tasks, list) and bool(tasks) and all(
            isinstance(task, str) and task in ALLOWED_TASKS for task in tasks
        )
        references = card.get("source_ids", [])
        references = references if isinstance(references, list) else []
        refs_total += len(references)
        valid_refs = [ref for ref in references if isinstance(ref, str) and ref in submitted_by_id]
        refs_resolved += len(valid_refs)
        checks.append({
            "index": index, "capability_id": card.get("capability_id"),
            "schema_valid": not missing and not wrong_types and task_valid,
            "missing_or_empty_fields": missing, "wrong_type_fields": wrong_types,
            "supported_task_types": task_valid,
            "all_references_resolve_to_submitted_sources": bool(references) and len(valid_refs) == len(references),
            "unresolved_source_ids": [str(ref) for ref in references if ref not in valid_refs],
        })
    valid_count = sum(item["schema_valid"] for item in checks)
    resolved_cards = sum(item.get("all_references_resolve_to_submitted_sources", False) for item in checks)
    gold_assertions = gold.get("assertions", [])
    source_keys = {source.get("source_key") for source in submitted}
    scoped_gold = [item for item in gold_assertions if item.get("source_key") in source_keys]
    assertions = artifact.get("result", {}).get("assertions")
    gold_result = {
        "status": "unevaluated_schema_mismatch",
        "reference_assertions_total": len(gold_assertions),
        "reference_assertions_in_submitted_source_scope": len(scoped_gold),
        "reference_assertions_outside_submitted_source_scope": len(gold_assertions) - len(scoped_gold),
        "precision": None, "recall": None, "f1": None,
        "reason": "Recorded output contains prose capability cards, not canonical assertion quadruples. "
                  "No automatic or hand-invented alignment is counted as model predictions.",
        "annotation_origin": gold.get("annotation_origin"),
        "independent_human_validation": False,
    }
    if isinstance(assertions, list):
        gold_result.update(evaluate_assertions(assertions, scoped_gold, source_keys))
        gold_result.update(status="evaluated_exact_assertion_agreement",
                           reason="Exact normalized quadruple agreement on the submitted source scope; "
                                  "this does not measure all semantic claims in the prose cards.")
    method_metrics = []
    ambiguous_metrics = []
    for card in cards:
        for metric in card.get("metrics", []):
            if metric in {"predict", "predict_proba", "decision_function", "transform", "fit"}:
                method_metrics.append({"capability_id": card.get("capability_id"), "value": metric})
            if metric == "score":
                ambiguous_metrics.append({"capability_id": card.get("capability_id"), "value": metric})
    return {
        "schema_version": "1.0", "mode": artifact.get("mode"), "model": artifact.get("model"),
        "evaluation_kind": "offline_recorded_extraction_audit", "new_model_calls": 0,
        "counts": {"submitted_sources": len(submitted), "ingested_corpus_sources": len(trusted_sources),
                   "returned_cards": total, "schema_valid_cards": valid_count},
        "structural_quality": {
            "required_fields": list(REQUIRED_FIELDS), "valid_card_rate": _rate(valid_count, total),
            "nonempty_field_counts": {field: sum(_nonempty(card.get(field)) for card in cards)
                                      for field in (*REQUIRED_FIELDS, "metrics")},
            "empty_metrics_allowed": "Transforms need not define evaluation metrics.",
            "duplicate_id_count": _duplicate_count([str(card.get("capability_id", "")) for card in cards]),
            "duplicate_name_count": _duplicate_count([str(card.get("name", "")) for card in cards]),
            "exact_duplicate_summary_count": _duplicate_count([str(card.get("summary", "")) for card in cards]),
            "duplicate_rate_definition": "Repeated normalized strings after the first occurrence / returned cards.",
            "duplicate_id_rate": _rate(_duplicate_count([str(card.get("capability_id", "")) for card in cards]), total),
            "semantic_duplicate_rate": None,
        },
        "provenance": {
            "reference_count": refs_total, "resolved_reference_count": refs_resolved,
            "reference_resolution_rate": _rate(refs_resolved, refs_total),
            "cards_with_all_references_resolved": resolved_cards,
            "card_reference_resolution_rate": _rate(resolved_cards, total),
            "verified_source_files": sum(item["file_sha256_matches"] for item in source_checks),
            "verified_source_locators": sum(item["locator_matches"] for item in source_checks),
            "verified_submitted_excerpts": sum(item["submitted_excerpt_matches"] for item in source_checks),
            "definition": "References exist in the exact submitted source set and current approved snapshots match. "
                          "This does not prove every cited source entails every card claim.",
            "source_checks": source_checks,
        },
        "automatic_review_flags": {
            "method_names_used_as_metrics": method_metrics,
            "ambiguous_score_metric_labels": ambiguous_metrics,
        },
        "gold_assertion_evaluation": gold_result,
        "semantic_precision": None, "semantic_recall": None,
        "card_checks": checks,
        "source_collection_issues": [{"source_key": item.get("source_key"), "error_type": "source_unavailable"}
                                     for item in issues],
    }


def _sanitize_text(value: str) -> str:
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{12,}\b", "[redacted-secret]", value)
    value = re.sub(r"(?:/(?:root|home|Users|private|tmp|var)/)[^\s\"'<>，。;]+", "[redacted-local-path]", value)
    value = re.sub(r"[A-Za-z]:\\[^\s\"'<>]+", "[redacted-local-path]", value)
    return value


def _public_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [_public_value(item) for item in value if isinstance(item, (str, int, float, bool))]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return None


def export_public_evidence(artifact: dict[str, Any], root: Path,
                           trusted_sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Allowlist public card fields, source locators and aggregate usage only."""
    if trusted_sources is None:
        trusted_sources, _ = collect_sources(root)
    trusted = {source["source_id"]: source for source in trusted_sources}
    public_sources = []
    for submitted in artifact.get("sources", []):
        source = trusted.get(submitted.get("source_id"))
        if source is None:
            continue
        locator = source["locator"]
        relative = locator.get("relative_path")
        if not relative:
            try:
                relative = str(Path(locator["path"]).resolve().relative_to(root.resolve()))
            except (ValueError, KeyError):
                relative = source["source_key"]
        url = urlsplit(source["uri"])
        if url.scheme in {"https", "http"} and url.netloc and not url.username:
            uri = urlunsplit((url.scheme, url.netloc, url.path, "", url.fragment))
        else:
            uri = "repository:" + relative
        public_sources.append({
            "source_id": source["source_id"], "source_key": source["source_key"],
            "uri": uri, "revision": source["revision"], "content_sha256": source["content_sha256"],
            "license": source.get("license"),
            "locator": {"relative_path": relative, "line_start": locator.get("line_start"),
                        "line_end": locator.get("line_end"), "symbol": locator.get("symbol")},
        })
    usage = artifact.get("usage", {})
    usage = {field: usage[field] for field in USAGE_FIELDS
             if isinstance(usage.get(field), int) and not isinstance(usage[field], bool) and usage[field] >= 0}
    return {
        "schema_version": "1.0", "mode": _public_value(artifact.get("mode")),
        "model": _public_value(artifact.get("model")), "created_at": _public_value(artifact.get("created_at")),
        "sources": public_sources,
        "capabilities": [{field: _public_value(card[field]) for field in CARD_FIELDS if field in card}
                         for card in _cards(artifact) if isinstance(card, dict)],
        "usage": usage,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "artifacts/ingestion/deepseek_extraction.json")
    parser.add_argument("--gold", type=Path, default=ROOT / "knowledge/extraction_gold.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/ingestion/extraction_evaluation.json")
    parser.add_argument("--export", type=Path, default=ROOT / "examples/evidence/knowledge_extraction.json")
    args = parser.parse_args()
    raw = args.input.read_bytes()
    artifact = json.loads(raw)
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    sources, _ = collect_sources(ROOT)
    report = evaluate_recorded_extraction(artifact, gold, ROOT, sources)
    report["input_artifact_sha256"] = _sha(raw)
    report["gold_sha256"] = _sha(args.gold.read_bytes())
    public = export_public_evidence(artifact, ROOT, sources)
    for path, content in ((args.output, report), (args.export, public)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "cards": report["counts"]["returned_cards"],
        "structural_valid_rate": report["structural_quality"]["valid_card_rate"],
        "source_reference_resolution_rate": report["provenance"]["reference_resolution_rate"],
        "gold_status": report["gold_assertion_evaluation"]["status"],
        "semantic_precision": None, "new_model_calls": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
