"""Read-only graph exploration and evidence presentation for visual clients.

The underlying SQLite property graph remains the source of truth. Presentation
labels never promote an extracted claim to a verified algorithm, and evidence
always includes the stored relationship path that connects it to the focus node.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from typing import Any

from capability_factory.knowledge import KnowledgeStore

KIND_LABELS = {
    "Capability": "算法能力", "Algorithm": "算法", "Transform": "数据处理",
    "Metric": "评价指标", "TaskType": "任务类型", "Environment": "依赖环境",
    "Source": "知识来源", "ValidationRun": "验证运行", "DatasetVersion": "数据版本",
    "Artifact": "代码制品", "FailureExperience": "失败与修复经验",
}
RELATION_LABELS = {
    "SOLVES": "适用任务", "DERIVED_FROM": "来源于", "USES": "使用",
    "REQUIRES": "依赖", "SUPERSEDES": "更新自", "EVALUATED_ON": "使用数据验证",
    "MEASURED_BY": "使用指标评估", "EVALUATES": "验证制品", "REPAIRS": "修复自",
    "IMPLEMENTS": "参考能力实现", "AVOIDED_BY": "由经验避免",
}
QUALITY_LABELS = {
    "above_prevalence": "验证集 AP 高于类别占比基线",
    "baseline_or_worse": "验证集 AP 未超过类别占比基线",
    "below_prevalence": "验证集 AP 未超过类别占比基线",
    "not_evaluated": "待评估质量",
}


def quality_label(status: Any) -> str:
    """Translate only known states, keeping unknown persisted states visible."""
    return QUALITY_LABELS.get(status, str(status) if status else "待评估质量")


def summarize_checks(value: Any) -> dict[str, Any]:
    """Represent real check lists without mistaking absent checks for passing."""
    checks = [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []
    passed = sum(item.get("passed") is True for item in checks)
    failed = sum(item.get("passed") is False for item in checks)
    mandatory = [item for item in checks if item.get("mandatory") is True]
    return {
        "items": checks, "total": len(checks), "passed": passed, "failed": failed,
        "unknown": len(checks) - passed - failed,
        "mandatory_total": len(mandatory),
        "mandatory_passed": sum(item.get("passed") is True for item in mandatory),
        "mandatory_failed": sum(item.get("passed") is False for item in mandatory),
        "all_mandatory_passed": all(item.get("passed") is True for item in mandatory) if mandatory else None,
    }


def _adjacency(edges: list[dict]) -> dict[str, list[tuple[str, dict]]]:
    adjacency = defaultdict(list)
    for edge in edges:
        adjacency[edge["source"]].append((edge["target"], edge))
        adjacency[edge["target"]].append((edge["source"], edge))
    for neighbors in adjacency.values():
        neighbors.sort(key=lambda item: (item[0], item[1]["id"]))
    return adjacency


def _paths(focus: str, adjacency: dict, hops: int) -> dict[str, list[dict]]:
    paths: dict[str, list[dict]] = {focus: []}
    queue = deque([focus])
    while queue:
        current = queue.popleft()
        if len(paths[current]) >= hops:
            continue
        for neighbor, edge in adjacency.get(current, []):
            if neighbor in paths:
                continue
            paths[neighbor] = paths[current] + [{
                "edge_id": edge["id"], "source": edge["source"], "target": edge["target"],
                "relation": edge["relation"],
                "relation_label": RELATION_LABELS.get(edge["relation"], edge["relation"]),
                "properties": edge.get("properties", {}),
            }]
            queue.append(neighbor)
    return paths


def _node(node: dict, degree: Counter, focus: str | None, paths: dict) -> dict:
    return {
        **node, "kind_label": KIND_LABELS.get(node["kind"], node["kind"]),
        "properties": {key: value for key, value in node["properties"].items()
                       if key not in {"content", "code", "source_code"}},
        "degree": degree[node["id"]], "focused": node["id"] == focus,
        "distance": len(paths[node["id"]]) if focus and node["id"] in paths else None,
    }


def _validation(store: KnowledgeStore, node: dict) -> dict:
    run_id = node["properties"].get("run_id") or node["id"].removeprefix("run:")
    report = store.get_run(run_id)
    if report is None:
        return {"run_id": run_id, "report_available": False, "status": node["properties"].get("status")}
    candidates = [item for item in report.get("candidates", []) if isinstance(item, dict)]
    selected = next((item for item in candidates if item.get("candidate_id") == report.get("selected_candidate_id")), {})
    quality = report.get("quality_status") or selected.get("quality_status")
    task = report.get("task_spec") if isinstance(report.get("task_spec"), dict) else {}
    return {
        "run_id": run_id, "report_available": True, "status": report.get("status"),
        "mode": report.get("mode"), "provider": report.get("provider"),
        "dataset_id": report.get("dataset_id"), "created_at": report.get("created_at"),
        "finished_at": report.get("finished_at"), "selected_candidate_id": report.get("selected_candidate_id"),
        "candidate_count": len(candidates), "quality_status": quality, "quality_label": quality_label(quality),
        "primary_metric": task.get("primary_metric", "average_precision"),
        "metrics": selected.get("metrics", report.get("metrics", {})),
        "checks": summarize_checks(selected.get("checks")),
        "report_url": f"/runs/{run_id}/report", "html_report_url": f"/runs/{run_id}/report.html",
    }


def _evidence(store: KnowledgeStore, focus: str, graph: dict, limit: int = 20) -> dict:
    """Expose linked evidence, never infer semantic validation from adjacency.

    Two hops capture capability <- artifact <- validation-run and capability ->
    source provenance. Edges unrelated to provenance (such as a shared dataset
    or a shared metric) are excluded to avoid presenting unrelated runs as proof.
    """
    allowed = {"DERIVED_FROM", "IMPLEMENTS", "EVALUATES", "AVOIDED_BY", "REPAIRS", "USES"}
    edges = [edge for edge in graph["edges"] if edge["relation"] in allowed]
    paths = _paths(focus, _adjacency(edges), 2)
    by_id = {node["id"]: node for node in graph["nodes"]}
    groups = {"Source": "sources", "ValidationRun": "validations", "Artifact": "artifacts",
              "FailureExperience": "failure_experiences"}
    result: dict[str, Any] = {key: [] for key in groups.values()}
    counts = Counter()
    ordered = sorted(paths, key=lambda identity: (len(paths[identity]), identity))
    for identity in ordered:
        node = by_id[identity]
        group = groups.get(node["kind"])
        if group is None:
            continue
        counts[group] += 1
        if len(result[group]) >= limit:
            continue
        item = {"node_id": identity, "label": node["label"], "path": paths[identity]}
        if node["kind"] == "ValidationRun":
            item.update(_validation(store, node))
        else:
            # Source content/code is deliberately excluded from the explorer.
            item["properties"] = {key: value for key, value in node["properties"].items()
                                  if key not in {"content", "code", "source_code"}}
        result[group].append(item)
    result["counts"] = {
        key: {"total": counts[key], "returned": len(result[key]), "omitted": counts[key] - len(result[key])}
        for key in groups.values()
    }
    result["truncated"] = any(counts[key] > len(result[key]) for key in groups.values())
    result["scope"] = "stored_provenance_paths_up_to_two_hops"
    result["interpretation"] = "关联证据需要结合路径、运行模式、检查项与指标，综合判断能力验证状态。"
    return result


def explore_graph(store: KnowledgeStore, *, focus: str | None = None, hops: int = 1,
                  kinds: list[str] | None = None, relations: list[str] | None = None,
                  query: str = "", limit: int = 120, edge_limit: int = 300) -> dict:
    """Return a deterministic, bounded graph view and explicit omission counts.

    Relation filters constrain traversal. Kind/text filters constrain displayed
    nodes after traversal; an existing focus is always retained for orientation.
    This prototype computes counts from the full SQLite graph snapshot, then
    limits the HTTP payload. It does not claim database-side pagination.
    """
    graph = store.graph()
    by_id = {node["id"]: node for node in graph["nodes"]}
    if focus and focus not in by_id:
        raise KeyError(focus)
    kinds_set, relations_set = set(kinds or []), set(relations or [])
    edges = [edge for edge in graph["edges"] if not relations_set or edge["relation"] in relations_set]
    adjacency = _adjacency(edges)
    paths = _paths(focus, adjacency, hops) if focus else {}
    scope = set(paths) if focus else set(by_id)
    search = query.strip().casefold()

    def matches(node):
        if kinds_set and node["kind"] not in kinds_set:
            return False
        searchable = " ".join([node["id"], node["label"], node["kind"],
                               json.dumps(node["properties"], ensure_ascii=False, sort_keys=True)])
        return not search or search in searchable.casefold()

    matched = {identity for identity in scope if matches(by_id[identity])}
    focus_retained = bool(focus and focus not in matched)
    if focus:
        matched.add(focus)
    matched_edges = [edge for edge in edges if edge["source"] in matched and edge["target"] in matched]
    degree = Counter(endpoint for edge in graph["edges"] for endpoint in (edge["source"], edge["target"]))
    ordered = sorted(matched, key=lambda identity: (
        identity != focus, len(paths[identity]) if focus else by_id[identity]["kind"] != "Capability",
        -degree[identity], identity,
    ))
    selected_ids = set(ordered[:limit])
    visible_edges = [edge for edge in matched_edges
                     if edge["source"] in selected_ids and edge["target"] in selected_ids]
    # Near-focus edges are retained first when a dense neighborhood hits the cap.
    visible_edges.sort(key=lambda edge: (focus not in (edge["source"], edge["target"]), edge["id"]))
    returned_edges = visible_edges[:edge_limit]
    kind_counts = Counter(node["kind"] for node in graph["nodes"])
    relation_counts = Counter(edge["relation"] for edge in graph["edges"])
    stats = {
        "total_nodes": len(graph["nodes"]), "total_edges": len(graph["edges"]),
        "scope_nodes": len(scope), "matched_nodes": len(matched), "matched_edges": len(matched_edges),
        "returned_nodes": len(selected_ids), "returned_edges": len(returned_edges),
        "omitted_nodes": len(matched) - len(selected_ids),
        "omitted_edges": len(matched_edges) - len(returned_edges),
        "hidden_by_filters": len(scope) - len(matched),
    }
    return {
        "schema_version": "1.0", "nodes": [_node(by_id[identity], degree, focus, paths) for identity in ordered[:limit]],
        "edges": [{**edge, "relation_label": RELATION_LABELS.get(edge["relation"], edge["relation"])}
                  for edge in returned_edges],
        "focus": _node(by_id[focus], degree, focus, paths) if focus else None,
        "filters": {"focus": focus, "hops": hops, "kinds": sorted(kinds_set),
                    "relations": sorted(relations_set), "q": query, "limit": limit, "edge_limit": edge_limit,
                    "traversal": "both_directions", "focus_retained_outside_filters": focus_retained},
        "stats": stats, "truncated": stats["omitted_nodes"] > 0 or stats["omitted_edges"] > 0,
        "facets": {
            "kinds": [{"value": kind, "label": KIND_LABELS.get(kind, kind), "count": count}
                      for kind, count in sorted(kind_counts.items())],
            "relations": [{"value": relation, "label": RELATION_LABELS.get(relation, relation), "count": count}
                          for relation, count in sorted(relation_counts.items())],
        },
        "evidence": _evidence(store, focus, graph) if focus else None,
    }


def capability_detail(store: KnowledgeStore, capability_id: str, version: int | None = None) -> dict:
    """Read one immutable capability version with its actual graph evidence."""
    with store._connection() as connection:
        rows = connection.execute(
            "SELECT version,content_sha256,status,origin,created_at FROM cf_capability_versions "
            "WHERE capability_id=? ORDER BY version DESC", (capability_id,),
        ).fetchall()
        if not rows:
            raise KeyError(capability_id)
        selected_version = version if version is not None else rows[0]["version"]
        row = connection.execute(
            "SELECT card_json FROM cf_capability_versions WHERE capability_id=? AND version=?",
            (capability_id, selected_version),
        ).fetchone()
        if row is None:
            raise KeyError(capability_id)
        card = json.loads(row["card_json"])
    node_id = f"capability:{capability_id}:v{selected_version}"
    graph = store.graph()
    graph_node = next((node for node in graph["nodes"] if node["id"] == node_id), None)
    adjacent = sorted({edge["target"] if edge["source"] == node_id else edge["source"]
                       for edge in graph["edges"] if node_id in (edge["source"], edge["target"])})
    versions = [{**dict(row), "node_id": f"capability:{capability_id}:v{row['version']}"} for row in rows[:100]]
    return {
        "schema_version": "1.0", "capability": card, "node_id": node_id,
        "node": graph_node, "latest_version": rows[0]["version"], "versions": versions,
        "version_count": len(rows), "versions_omitted": max(0, len(rows) - len(versions)),
        "related_node_ids": adjacent[:100], "related_nodes_omitted": max(0, len(adjacent) - 100),
        "evidence": _evidence(store, node_id, graph) if graph_node else None,
    }
