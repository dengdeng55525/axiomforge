"""Deterministic quality/resource analysis of measured candidates within one run."""

from __future__ import annotations

import math


def _number(value, *, minimum=0, maximum=None):
    return (type(value) in {int, float} and math.isfinite(value)
            and value >= minimum and (maximum is None or value <= maximum))


def analyze_resources(report: dict) -> dict:
    """Expose a Pareto frontier and paired child changes without changing selection.

    AP is maximized; fit seconds and peak worker RSS are minimized. Missing
    observations exclude a point instead of receiving a fabricated zero cost.
    Values compare candidates in the same immutable run protocol, not runs with
    different datasets/hardware. One observation cannot establish a speedup.
    """
    rows, excluded = [], []
    for candidate in report.get("candidates", []):
        identity = candidate["candidate_id"]
        metrics, resources = candidate.get("metrics") or {}, candidate.get("resources") or {}
        observations = {"average_precision": metrics.get("average_precision"),
                        "fit_seconds": resources.get("fit_seconds"),
                        "peak_rss_mib": resources.get("peak_rss_mib")}
        invalid = [name for name, value in observations.items()
                   if not _number(value, maximum=1 if name == "average_precision" else None)]
        if candidate.get("status") != "passed" or invalid:
            excluded.append({"candidate_id": identity,
                             "reason": "failed_or_incomplete_validation" if candidate.get("status") != "passed" else "missing_or_invalid_measurements",
                             "fields": invalid})
            continue
        rows.append({"candidate_id": identity, **observations,
                     "parent_id": candidate.get("parent_id") or (candidate.get("plan") or {}).get("parent_id"),
                     "predict_seconds": resources.get("predict_seconds") if _number(resources.get("predict_seconds")) else None})

    def dominates(left, right):
        a = (-left["average_precision"], left["fit_seconds"], left["peak_rss_mib"])
        b = (-right["average_precision"], right["fit_seconds"], right["peak_rss_mib"])
        return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))

    for row in rows:
        row["dominated_by"] = sorted(other["candidate_id"] for other in rows if dominates(other, row))
        row["pareto_optimal"] = not row["dominated_by"]
    rows.sort(key=lambda row: (-row["average_precision"], row["fit_seconds"], row["candidate_id"]))
    by_id = {row["candidate_id"]: row for row in rows}
    mutations = []
    for row in rows:
        parent = by_id.get(row["parent_id"])
        if parent is not None:
            mutations.append({
                "parent_id": parent["candidate_id"], "candidate_id": row["candidate_id"],
                "ap_delta": row["average_precision"] - parent["average_precision"],
                "fit_seconds_delta": row["fit_seconds"] - parent["fit_seconds"],
                "peak_rss_mib_delta": row["peak_rss_mib"] - parent["peak_rss_mib"],
                "dominates_parent": dominates(row, parent),
            })
    return {
        "schema_version": "1.0", "analysis_version": "pareto-observations-v1",
        "run_id": report.get("run_id"), "scope": "within_run_validation_observations",
        "objectives": {"average_precision": "maximize", "fit_seconds": "minimize", "peak_rss_mib": "minimize"},
        "selected_candidate_id": report.get("selected_candidate_id"),
        "selection_policy": "validation_ap_desc_then_candidate_wall_seconds_asc",
        "frontier_candidate_ids": [row["candidate_id"] for row in rows if row["pareto_optimal"]],
        "candidates": rows, "excluded": excluded, "parent_child_changes": mutations,
        "measurement_repetitions": 1 if rows else 0,
        "limitations": ["同次运行的验证集 AP、训练耗时和 worker 峰值 RSS 观测，不能跨任务混排。",
                        "单次耗时受负载与测量噪声影响，不代表稳定加速或统计显著性。",
                        "Pareto 分析提供资源权衡依据，不改变原有 AP 优先选择规则。",
                        "worker RSS 不含 LLM 服务显存；封存测试集没有用于优化。"],
    }
