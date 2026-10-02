#!/usr/bin/env python3
"""Build documentation snapshots from checked-in evidence in an isolated store.

This helper never loads .env, calls a provider, or opens the live knowledge DB.
Its JSON output is consumed by web/scripts/capture-docs.mjs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from capability_factory.api import _dataset_catalog, _provider_catalog
from capability_factory.graph_presentation import capability_detail, explore_graph
from capability_factory.inference import load_inference_profiles, local_profile_metadata
from capability_factory.knowledge import KnowledgeStore
from capability_factory.knowledge_governance import validate_store
from capability_factory.observability import build_agent_trace
from capability_factory.settings import Settings


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = Settings(root=root)  # Deliberately bypass load_settings/.env.
    reports = {}
    sources = []
    for path in sorted((root / "examples/evidence").glob("*/report.json")):
        original = path.read_bytes()
        report = json.loads(original)
        report["agent_trace"] = build_agent_trace(report)
        reports[report["run_id"]] = report
        sources.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(original).hexdigest(),
            "run_id": report["run_id"],
            "mode": report.get("mode"),
            "provider": report.get("provider"),
            "metrics_modified": False,
        })

    store = KnowledgeStore(":memory:")
    try:
        ingestion = store.ingest_sources(root)
        for report in reports.values():
            store.save_run(report)
        capabilities = store.list_capabilities()
        details = {
            card["capability_id"]: capability_detail(store, card["capability_id"])
            for card in capabilities
        }
        views = {"": explore_graph(store, limit=120)}
        for card in capabilities:
            node_id = f"capability:{card['capability_id']}:v{card['version']}"
            views[node_id] = explore_graph(store, focus=node_id, hops=1)
        result = {
            "reports": reports,
            "runs": store.list_runs(),
            "capabilities": capabilities,
            "capability_details": details,
            "graph": store.graph(),
            "graph_views": views,
            "knowledge_quality": validate_store(store),
            "config": {
                "datasets": _dataset_catalog(settings),
                "providers": _provider_catalog(settings),
                "limits": {
                    "max_candidates": {"min": 1, "max": 6},
                    "max_repairs": {"min": 0, "max": 2},
                },
            },
            "profiles": {
                **load_inference_profiles(root),
                "active_local": local_profile_metadata(settings),
            },
            "provenance": {
                "reports": sources,
                "graph": {
                    "method": "KnowledgeStore(':memory:').ingest_sources + save_run",
                    "seed": "knowledge/seed_capabilities.json",
                    "source_manifest": ingestion["source_manifest"],
                    "live_database_accessed": False,
                    "llm_extraction_invoked": False,
                },
                "environment": {
                    "method": "Settings(root=repository), without .env or credentials",
                    "api_connectivity_probed": False,
                    "local_model_started": False,
                },
            },
        }
        # Source locators remain portable in both browser snapshots and the
        # published manifest; preserve every hash, line number and source ID.
        serialized = json.dumps(result, ensure_ascii=False)
        print(serialized.replace(root.as_posix() + "/", ""))
    finally:
        store.close()


if __name__ == "__main__":
    main()
