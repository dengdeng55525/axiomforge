"""HTTP-only Streamlit client for the algorithm capability factory.

Start with: streamlit run ui/app.py --server.address 127.0.0.1
The UI never imports an evaluator or executes generated Python.
"""

from __future__ import annotations

import html
import json
import math
import os
from typing import Any
from urllib.parse import quote, urlparse

import httpx
import streamlit as st

API_URL = os.environ.get("ALGOFORGE_API_URL", "http://127.0.0.1:8000").rstrip("/")
TERMINAL = {"completed", "passed", "failed", "cancelled", "error", "succeeded"}
MODE_LABELS = {
    "deepseek": "真实 LLM / DeepSeek API",
    "openai": "OpenAI / Responses API",
    "local_http": "本地 14B / HTTP 服务",
    "real": "真实 LLM 调用",
    "api": "真实 LLM / API",
    "mock": "模拟 LLM / 仅验证工程流程",
    "replay": "历史回放 / 非当前实时执行",
}
PROVIDER_LABELS = {
    "deepseek": "DeepSeek V4.1 API",
    "openai": "OpenAI / Responses API",
    "local_http": "本地 14B · OpenAI 兼容接口",
    "mock": "Mock · 离线演示",
}
STAGE_DEFINITIONS = [
    ("interpret", "🧭 需求理解", "把自然语言约束转成可验证任务"),
    ("retrieve", "🔎 证据检索", "从知识库与图谱召回依据"),
    ("plan", "🗺️ 候选规划", "生成可比较的算法方案"),
    ("generate", "🧩 代码生成", "按受限语法生成候选 Pipeline"),
    ("validate", "🧪 独立验证", "隔离进程训练并计算指标"),
    ("repair", "🛠️ 有限修复", "根据失败证据修复，最多两轮"),
    ("writeback", "🧠 经验沉淀", "写入版本化能力与失败经验"),
    ("report", "📄 报告交付", "汇总证据、资源与可复现制品"),
]
EVENT_STAGE_ALIASES = {
    "INTERPRET": "interpret", "INTERPRETER": "interpret", "TASK_INTERPRETED": "interpret", "SPEC_VALIDATED": "interpret", "RECEIVED": "interpret",
    "RETRIEVE": "retrieve", "EVIDENCE": "retrieve", "KNOWLEDGE_RETRIEVED": "retrieve",
    "PLAN": "plan", "PLANNER": "plan", "PLANNED": "plan", "CANDIDATE_PLANNED": "plan", "BEAM_EXPANDED": "plan", "COMPARED": "plan",
    "GENERATE": "generate", "CODER": "generate", "CODE_GENERATED": "generate",
    "VALIDATE": "validate", "VALIDATING": "validate", "VERIFY": "validate", "VERIFIED": "validate",
    "REVIEW": "repair", "REPAIR": "repair", "REPAIRED": "repair", "REPAIR_PLANNED": "repair", "FAILURE_INJECTED": "repair",
    "WRITEBACK": "writeback", "MEMORY": "writeback", "CURATOR": "writeback", "RECORDED": "writeback",
    "REPORT": "report", "COMPLETED": "report", "PASSED": "report",
}
DEFAULTS = {
    "bank": ("预测客户是否订购银行定期存款；仅使用通话前可得特征，禁止 duration。"
             "比较两个候选，使用验证集 AP 选择方案，输出来源、检查、资源和修复记录。"),
    "sms": ("构建短信垃圾信息分类能力，比较 TF-IDF 与线性或朴素贝叶斯方案。"
            "保持训练、验证、测试隔离，报告 AP、F1 和接口检查结果。"),
}

STATUS_LABELS = {
    "passed": "通过",
    "completed": "已完成",
    "succeeded": "已完成",
    "failed": "未通过",
    "error": "错误",
    "cancelled": "已取消",
    "running": "执行中",
    "queued": "排队中",
    "pending": "待执行",
    "proposed": "待验证",
    "verified": "已验证",
    "extracted": "已抽取",
    "draft": "草稿",
    "deprecated": "已废弃",
}
KIND_LABELS = {
    "TaskType": "任务类型", "Capability": "算法能力", "Algorithm": "算法",
    "Transform": "数据变换", "DatasetVersion": "数据版本", "Metric": "评价指标",
    "Environment": "运行环境", "Source": "证据来源", "Artifact": "代码制品",
    "ValidationRun": "验证运行", "FailureExperience": "失败经验",
}
KIND_COLORS = {
    "TaskType": "#6d5dfc", "Capability": "#087f8c", "Algorithm": "#2563eb",
    "Transform": "#16a34a", "DatasetVersion": "#d97706", "Metric": "#db2777",
    "Environment": "#64748b", "Source": "#9333ea", "Artifact": "#0f766e",
    "ValidationRun": "#0891b2", "FailureExperience": "#dc2626",
}
RELATION_LABELS = {
    "SOLVES": "解决", "IMPLEMENTS": "实现", "USES": "使用", "REQUIRES": "依赖",
    "DERIVED_FROM": "派生自", "EVALUATED_ON": "评测于", "EVALUATES": "评测",
    "MEASURED_BY": "由指标测量", "REPAIRS": "修复", "SUPERSEDES": "替代",
    "AVOIDED_BY": "规避方式",
}


def status_label(value: Any) -> str:
    return STATUS_LABELS.get(str(value).lower(), str(value) if value not in (None, "") else "未记录")


def format_metric(value: Any, key: str = "") -> str:
    value = number(value)
    if value is None:
        return "—"
    if "lift" in key.lower():
        return f"{value:.2f}×"
    return f"{value:.4f}"


def records(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def number(value: Any) -> float | None:
    if isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def display(value: Any) -> str:
    if value is None:
        return "未记录"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def metric_value(candidate: dict[str, Any], *names: str) -> float | None:
    """Read a metric without treating a missing observation as zero."""
    groups = [candidate.get("metrics"), candidate]
    for group in groups:
        if not isinstance(group, dict):
            continue
        for name in names:
            for key in (name, name.lower(), name.upper()):
                value = number(group.get(key))
                if value is not None:
                    return value
    return None


def event_name(event: dict[str, Any]) -> str:
    for key in ("event_type", "type", "step", "event", "name"):
        value = event.get(key)
        if value:
            return str(value).upper()
    return ""


def stage_state(run: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, str]:
    """Infer a display state from persisted events without inventing run results."""
    states = {key: "pending" for key, _, _ in STAGE_DEFINITIONS}
    seen: list[str] = []
    for event in events:
        key = EVENT_STAGE_ALIASES.get(event_name(event))
        if key and key not in seen:
            seen.append(key)
        if key:
            states[key] = "done"
    status = str(run.get("status", "")).lower()
    if status in {"running", "queued"} and seen:
        current = seen[-1]
        states[current] = "running"
        for key, _, _ in STAGE_DEFINITIONS:
            if key == current:
                break
            states[key] = "done"
    elif status in TERMINAL:
        for key in seen:
            states[key] = "done"
        states["report"] = "done" if status in {"passed", "completed", "succeeded"} else "failed"
        if status in {"failed", "error", "cancelled"} and seen:
            states[seen[-1]] = "failed"
    return states


def mode_label(value: Any) -> str:
    if value is None:
        return "模式未记录：不推断真实调用"
    return MODE_LABELS.get(str(value).lower(), f"未识别模式：{value}")


def run_mode_label(run: dict[str, Any]) -> str:
    """Keep provider identity and service deployment visible in reports."""
    if run.get("mode") in {"mock", "replay"}:
        return mode_label(run["mode"])
    if run.get("provider") == "openai":
        deployment = (run.get("provider_metadata") or {}).get("deployment")
        if deployment == "official_api":
            return "OpenAI 官方 API · Responses"
        if deployment == "openai_compatible_api":
            return "OpenAI 兼容服务 · Responses"
        return PROVIDER_LABELS["openai"]
    return PROVIDER_LABELS.get(str(run.get("provider")), mode_label(run.get("mode")))


def api(method: str, path: str, body: dict[str, Any] | None = None, raw: bool = False) -> Any:
    """Talk only to the administrator-configured backend; no model key in the UI."""
    parsed = urlparse(API_URL)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("ALGOFORGE_API_URL 必须是有效的 HTTP(S) API 地址。")
    try:
        # Backend traffic stays direct; global cloud-model proxies must not intercept it.
        with httpx.Client(timeout=httpx.Timeout(15.0, connect=3.0), trust_env=False) as client:
            response = client.request(method, API_URL + path, json=body)
        response.raise_for_status()
        return response.text if raw else response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise RuntimeError(f"API 返回 {exc.response.status_code}：{detail}") from exc
    except (httpx.RequestError, ValueError) as exc:
        raise RuntimeError(f"无法读取 API：{type(exc).__name__}。检查服务是否启动及 API 地址。") from exc


def run_path(run_id: str) -> str:
    return "/runs/" + quote(run_id, safe="")


def get_run(run_id: str) -> dict[str, Any] | None:
    try:
        result = api("GET", run_path(run_id))
        if not isinstance(result, dict):
            raise RuntimeError("运行接口未返回 JSON 对象。")
        nested = result.get("report")
        return {**result, **nested} if isinstance(nested, dict) else result
    except RuntimeError as exc:
        st.error(str(exc))
        return None


def candidate_rows(candidates: Any) -> list[dict[str, Any]]:
    rows = []
    for candidate in records(candidates):
        row = {"candidate_id": candidate.get("candidate_id"),
               "status": candidate.get("status"),
               "quality_status": candidate.get("quality_status"),
               "artifact_id": candidate.get("artifact_id")}
        for group in ("metrics", "resources"):
            values = candidate.get(group)
            if isinstance(values, dict):
                for key, value in values.items():
                    row[f"{group}.{key}"] = display(value) if isinstance(value, (dict, list)) else value
        rows.append(row)
    return rows


def render_stage_timeline(run: dict[str, Any], events: list[dict[str, Any]]) -> None:
    states = stage_state(run, events)
    cards = []
    icons = {"done": "✓", "running": "●", "failed": "!", "pending": "○"}
    for key, title, subtitle in STAGE_DEFINITIONS:
        state = states[key]
        color = {"done": "#159957", "running": "#f59e0b", "failed": "#d64545", "pending": "#9aabba"}[state]
        cards.append(
            f"<div class='stage-card stage-{state}'>"
            f"<div class='stage-icon' style='color:{color}'>{icons[state]}</div>"
            f"<div><b>{html.escape(title)}</b><small>{html.escape(subtitle)}</small></div></div>"
        )
    st.markdown("<div class='stage-track'>" + "".join(cards) + "</div>", unsafe_allow_html=True)


def render_candidate_cards(candidates: list[dict[str, Any]], selected_id: str | None = None) -> None:
    if not candidates:
        st.info("当前暂无候选，验证完成后会在这里显示对比卡片。")
        return
    columns = st.columns(min(3, len(candidates)))
    for index, candidate in enumerate(candidates):
        col = columns[index % len(columns)]
        candidate_id = str(candidate.get("candidate_id", f"candidate-{index + 1}"))
        status = str(candidate.get("status", "pending"))
        badge_class = "good" if status in {"passed", "succeeded"} else "bad" if status in {"failed", "error"} else "wait"
        ap = metric_value(candidate, "average_precision", "AP", "ap")
        lift = metric_value(candidate, "lift_at_10pct", "lift10", "lift_at_10")
        roc = metric_value(candidate, "roc_auc", "ROC_AUC", "auc")
        marker = " · 已选中" if selected_id and candidate_id == selected_id else ""
        with col:
            st.markdown(
                f"<div class='candidate-card'><div class='candidate-top'><b>{html.escape(candidate_id)}</b>"
                f"<span class='badge {badge_class}'>{html.escape(status)}{marker}</span></div>"
                f"<div class='candidate-algo'>{html.escape(str(candidate.get('algorithm') or (candidate.get('plan') or {}).get('algorithm') or '方案'))}</div>"
                f"<div class='candidate-stat'><span>AP</span><strong>{'—' if ap is None else f'{ap:.4f}'}</strong></div>"
                f"<div class='candidate-stat'><span>ROC-AUC</span><strong>{'—' if roc is None else f'{roc:.4f}'}</strong></div>"
                f"<div class='candidate-stat'><span>Lift@10%</span><strong>{'—' if lift is None else f'{lift:.2f}×'}</strong></div>"
                "</div>", unsafe_allow_html=True
            )


def render_metric_chart(candidates: list[dict[str, Any]]) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.caption("未安装 Plotly，保留表格指标。")
        return
    rows = []
    for index, candidate in enumerate(candidates):
        rows.append((str(candidate.get("candidate_id", index + 1)), metric_value(candidate, "average_precision", "AP", "ap"),
                     metric_value(candidate, "roc_auc", "ROC_AUC", "auc"), metric_value(candidate, "lift_at_10pct", "lift10")))
    rows = [row for row in rows if any(value is not None for value in row[1:])]
    if not rows:
        return
    figure = go.Figure()
    for label, name, color in (("AP", 1, "#0f766e"), ("ROC-AUC", 2, "#2563eb"), ("Lift@10%", 3, "#d97706")):
        values = [row[name] if row[name] is not None else None for row in rows]
        if any(value is not None for value in values):
            figure.add_bar(name=label, x=[row[0] for row in rows], y=values, marker_color=color)
    figure.update_layout(height=280, barmode="group", margin={"l": 20, "r": 20, "t": 20, "b": 20},
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         legend={"orientation": "h", "y": 1.12}, yaxis={"title": "验证值"})
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_resources(run: dict[str, Any]) -> None:
    candidates = records(run.get("candidates"))
    rows = []
    for candidate in candidates:
        resources = candidate.get("resources") if isinstance(candidate.get("resources"), dict) else {}
        rows.append({"候选": candidate.get("candidate_id"), "状态": candidate.get("status"),
                     "训练秒数": resources.get("fit_seconds", resources.get("fit_s")),
                     "峰值 RSS(MiB)": resources.get("peak_rss_mib", resources.get("peak_rss")),
                     "验证进程": resources.get("pid")})
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    usage = run.get("usage") if isinstance(run.get("usage"), dict) else {}
    st.caption(f"LLM 请求 {display(usage.get('calls'))} 次 · 输入 token {display(usage.get('input_tokens'))} · 输出 token {display(usage.get('output_tokens'))}。")


def _check_rows(checks: Any) -> list[dict[str, str]]:
    """Flatten validator checks into a human-readable table."""
    if not isinstance(checks, dict):
        return []
    rows = []
    for key, value in checks.items():
        if isinstance(value, dict):
            for child, result in value.items():
                rows.append({"检查项": f"{key} / {child}", "结果": status_label(result) if isinstance(result, str) else ("通过" if result is True else "未通过" if result is False else display(result))})
        else:
            rows.append({"检查项": str(key), "结果": "通过" if value is True else "未通过" if value is False else display(value)})
    return rows


def _human_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    plan = candidate.get("plan") if isinstance(candidate.get("plan"), dict) else {}
    metrics = candidate.get("metrics") if isinstance(candidate.get("metrics"), dict) else {}
    checks = candidate.get("checks") if isinstance(candidate.get("checks"), dict) else {}
    resources = candidate.get("resources") if isinstance(candidate.get("resources"), dict) else {}
    return {
        "候选": candidate.get("candidate_id", "未命名"),
        "算法": plan.get("algorithm") or candidate.get("algorithm") or "未记录",
        "变体": plan.get("variant") or "默认",
        "状态": status_label(candidate.get("status")),
        "质量门槛": status_label(candidate.get("quality_status")),
        "AP": format_metric(metrics.get("average_precision", metrics.get("AP")), "ap"),
        "ROC-AUC": format_metric(metrics.get("roc_auc", metrics.get("ROC_AUC")), "auc"),
        "F1": format_metric(metrics.get("f1", metrics.get("f1_at_0_5")), "f1"),
        "Lift@10%": format_metric(metrics.get("lift_at_10pct", metrics.get("lift10")), "lift"),
        "通过检查": sum(1 for row in _check_rows(checks) if row["结果"] == "通过"),
        "总检查": len(_check_rows(checks)),
        "训练耗时": resources.get("fit_seconds", resources.get("fit_s")),
    }


def render_human_report(run: dict[str, Any], summary: dict[str, Any] | None = None) -> None:
    """Present a decision-oriented report; raw JSON remains an advanced evidence view."""
    candidates = records(run.get("candidates"))
    selected_id = run.get("selected_candidate_id")
    selected = next((item for item in candidates if item.get("candidate_id") == selected_id), None)
    task_spec = run.get("task_spec") if isinstance(run.get("task_spec"), dict) else {}
    primary = str(task_spec.get("primary_metric", "average_precision"))
    quality = str(run.get("quality_status", ""))
    status = str(run.get("status", ""))
    if status in {"passed", "completed", "succeeded"} and selected:
        st.success(f"验证完成：已选择 {selected_id}，质量门槛为“{status_label(quality)}”。")
    elif status in {"failed", "error"}:
        st.error("验证结束但未达到质量门槛。下面保留失败证据和修复轨迹，便于复盘。")
    elif status == "cancelled":
        st.warning("运行已取消，已产生的验证事实仍然保留。")
    else:
        st.info(f"当前状态：{status_label(status)}。候选和事件会随着服务端进度更新。")

    overview = st.columns(4)
    overview[0].metric("运行状态", status_label(status))
    overview[1].metric("任务数据", str(run.get("dataset_id", task_spec.get("dataset_id", "未记录"))))
    overview[2].metric("候选数量", len(candidates))
    overview[3].metric("主指标", primary.replace("average_precision", "AP").upper())

    if selected:
        plan = selected.get("plan") if isinstance(selected.get("plan"), dict) else {}
        metrics = selected.get("metrics") if isinstance(selected.get("metrics"), dict) else {}
        st.markdown("#### 选择依据")
        st.markdown(
            f"系统在同一数据切分和预算下比较了 **{len(candidates)}** 个候选，"
            f"按预注册主指标 **{primary.replace('average_precision', 'AP').upper()}** 选择 **{selected_id}**。"
            f"该候选使用 **{plan.get('algorithm', '未记录')}**，当前观测值为 **{format_metric(metrics.get(primary), primary)}**。"
        )
        if run.get("provenance"):
            provenance = run["provenance"]
            st.caption(f"评测口径：{display(provenance.get('split', '验证集'))} · 数据和特征约束来自后端固定协议。")
        if quality in {"passed", "verified", "quality_passed"}:
            st.info("交付建议：本次候选通过了原型质量门槛，可进入人工复核或预发布评审；最终上线仍需在业务数据、封存测试集和监控告警下重新验收。")
        else:
            st.warning("交付建议：当前结果只适合作为失败复盘或继续修复的输入，不能作为生产模型结论。")
    elif not candidates:
        st.caption("当前暂无候选。")

    st.markdown("#### 候选对比")
    if candidates:
        st.dataframe([_human_candidate(item) for item in candidates], use_container_width=True, hide_index=True)
        render_metric_chart(candidates)
    else:
        st.info("暂无候选结果。")

    if selected:
        with st.expander("中间过程：选中方案的规划、检查、修复和资源", expanded=False):
            st.markdown("#### 选中方案详情")
            detail_cols = st.columns(2)
            plan = selected.get("plan") if isinstance(selected.get("plan"), dict) else {}
            detail_cols[0].markdown(f"**算法方案**  \n{display(plan.get('algorithm'))} · {display(plan.get('variant'))}")
            detail_cols[0].markdown(f"**代码制品**  \n`{display(selected.get('artifact_id'))}`")
            detail_cols[1].markdown(f"**代码校验**  \n`{display(selected.get('code_sha256'))}`")
            detail_cols[1].markdown(f"**修复次数**  \n{len(records(selected.get('repairs')))} 次")
            checks = _check_rows(selected.get("checks"))
            if checks:
                st.dataframe(checks, use_container_width=True, hide_index=True)
            tabs = st.tabs(["规划与依据", "修复记录", "资源观测"])
            with tabs[0]:
                st.write(plan.get("rationale", plan.get("reason", "规划依据由候选事实和召回证据组成。")))
                evidence = plan.get("evidence", plan.get("retrieved_evidence"))
                if evidence:
                    st.dataframe([{ "来源": item.get("source_id", item.get("source", "")), "摘要": item.get("summary", item.get("text", display(item))) } if isinstance(item, dict) else {"来源": "证据", "摘要": item} for item in records(evidence)], use_container_width=True, hide_index=True)
            with tabs[1]:
                repairs = records(selected.get("repairs"))
                st.dataframe([{ "轮次": item.get("attempt", index + 1), "结果": status_label(item.get("status")), "原因": item.get("error", item.get("diagnosis", "未记录")) } for index, item in enumerate(repairs)], use_container_width=True, hide_index=True) if repairs else st.caption("本候选没有修复记录。")
            with tabs[2]:
                resources = selected.get("resources") if isinstance(selected.get("resources"), dict) else {}
                st.dataframe([{ "训练耗时（秒）": resources.get("fit_seconds", resources.get("fit_s")), "预测耗时（秒）": resources.get("predict_seconds", resources.get("predict_s")), "峰值内存（MiB）": resources.get("peak_rss_mib", resources.get("peak_rss")), "进程限制": display(resources.get("limits")) }], use_container_width=True, hide_index=True)
    warning_items = run.get("warnings") if isinstance(run.get("warnings"), list) else []
    if warning_items:
        st.warning("；".join(display(item) for item in warning_items))


def show_identity(run: dict[str, Any]) -> None:
    st.info(run_mode_label(run))
    columns = st.columns(5)
    columns[0].metric("状态", display(run.get("status")))
    columns[1].metric("质量门槛", display(run.get("quality_status")))
    columns[2].metric("候选数", len(records(run.get("candidates"))))
    columns[3].metric("选中候选", display(run.get("selected_candidate_id")))
    timing = run.get("timing") if isinstance(run.get("timing"), dict) else {}
    elapsed = timing.get("wall_seconds", timing.get("elapsed_s", timing.get("total_s", timing.get("wall_time_s"))))
    columns[4].metric("运行耗时（秒）", display(elapsed))
    st.caption("运行 ID：" + display(run.get("run_id")) + " · 模型：" + display(run.get("model")))


def monitor() -> None:
    run_id = st.session_state.get("active_run", "")
    if not run_id:
        st.info("提交任务，或在左侧输入历史运行 ID。")
        return
    run = get_run(run_id)
    if run is None:
        return
    show_identity(run)
    try:
        event_payload = api("GET", run_path(run_id) + "/events")
        events = records(event_payload.get("events")) if isinstance(event_payload, dict) else []
    except RuntimeError:
        events = []
    render_stage_timeline(run, events)
    current_status = str(run.get("status", "")).lower()
    if current_status in {"queued", "running"}:
        st.progress(0.38 if current_status == "queued" else 0.72,
                    text="任务已进入执行队列" if current_status == "queued" else "Agent 正在处理，请保留此页面或稍后刷新")
    elif current_status in {"passed", "completed", "succeeded"}:
        st.success("流程完成：候选已通过独立验证，报告和制品可在“代码与报告”查看。")
    elif current_status in {"failed", "error"}:
        st.error("流程结束但未通过质量门槛；请查看失败原因、检查项和修复轨迹。")
    elif current_status == "cancelled":
        st.warning("流程已取消，已产生的事件和资源记录仍然保留。")
    if str(run.get("status", "")).lower() not in TERMINAL:
        if st.button("取消当前任务", key="cancel_active"):
            try:
                result = api("POST", run_path(run_id) + "/cancel")
                st.json(result)
                st.caption("取消结果以服务端状态和执行器回收记录为准。")
            except RuntimeError as exc:
                st.error(str(exc))
    if run.get("warnings"):
        st.warning("此运行包含警告，请在答辩和报告中保留。")
        with st.expander("查看警告原文", expanded=False):
            st.json(run["warnings"])
    rows = candidate_rows(run.get("candidates"))
    if rows:
        st.subheader("候选验证进度")
        st.dataframe(rows, use_container_width=True, hide_index=True)
        render_candidate_cards(records(run.get("candidates")), run.get("selected_candidate_id"))
        render_metric_chart(records(run.get("candidates")))
        with st.expander("训练资源与 LLM 预算", expanded=False):
            render_resources(run)
    with st.expander("中间过程：事件时间线与 Agent 事件", expanded=False):
        try:
            if events:
                event_rows = [{"时间": event.get("timestamp", event.get("created_at", "")),
                               "步骤": event_name(event) or "事件",
                               "详情": display(event.get("detail", event.get("payload", event.get("data", event))))}
                              for event in events]
                st.dataframe(event_rows, use_container_width=True, hide_index=True)
                with st.expander("完整事件 JSON"):
                    st.json(events)
            else:
                st.caption("尚无已记录事件。")
        except RuntimeError as exc:
            st.warning(str(exc))
    with st.expander("需求、数据与预算约束"):
        st.json(run.get("task_spec") or {})
        st.json(run.get("provenance") or {})
    with st.expander("LLM 用量与计时"):
        st.json({"usage": run.get("usage"), "timing": run.get("timing")})


def submission_view() -> None:
    st.subheader("从需求开始，保留每一步证据")
    st.caption("银行营销为主场景，短信分类检验同一流程的跨场景能力。数据与评价协议由后端固定。")
    dataset = st.radio("选择任务数据", ["bank", "sms"], horizontal=True,
                       format_func=lambda value: "银行营销响应" if value == "bank" else "短信垃圾信息分类")
    with st.form("new_run"):
        description = st.text_area("中文能力需求", value=DEFAULTS[dataset],
                                   height=130, key=f"description_{dataset}")
        col1, col2, col3 = st.columns(3)
        provider = col1.selectbox("LLM 来源", ["deepseek", "openai", "local_http", "mock"],
                                  format_func=lambda value: PROVIDER_LABELS[value])
        search = col2.selectbox("候选搜索", ["compare", "beam"],
                                format_func=lambda value: "并列候选比较" if value == "compare"
                                else "Beam Search")
        candidates = col3.selectbox("候选上限", [2, 4, 6], index=0)
        with st.expander("修复、知识与演示设置"):
            option1, option2 = st.columns(2)
            max_repairs = option1.slider("每候选最多修复次数", 0, 2, 2)
            orchestration = option2.selectbox("编排方式", ["multi_role", "single_shot"],
                                              format_func=lambda value: "多角色协作（推荐）" if value == "multi_role" else "单次生成（消融）")
            use_graph = st.checkbox("使用知识图谱证据检索", value=True)
            use_retrieval = st.checkbox("注入文本证据上下文", value=True)
            inject_failure = st.checkbox("注入标记故障（仅用于修复演示）", value=False)
            st.caption("故障注入结果应与自然错误分开统计。候选数是上限，失败或预算耗尽可能提前停止。")
            if provider == "local_http":
                st.info("本地 14B 使用 OpenAI 兼容 HTTP 接口。当前服务会读取 LOCAL_LLM_BASE_URL；界面只提交 provider，不接触模型密钥。")
            if provider == "openai":
                st.info("服务端通过 OpenAI 官方 Python SDK 调用 Responses 接口；实际 API 服务方、模型和凭证由后端配置，界面仅提交 provider。")
        submitted = st.form_submit_button("提交并开始验证", type="primary")
    if submitted:
        if not description.strip():
            st.error("请填写能力需求。")
        else:
            try:
                result = api("POST", "/runs", {
                    "description": description.strip(), "dataset_id": dataset,
                    "provider": provider, "max_candidates": candidates,
                    "max_repairs": max_repairs, "use_graph": use_graph,
                    "use_retrieval": use_retrieval, "orchestration": orchestration,
                    "search": search, "inject_failure": inject_failure,
                })
                if not isinstance(result, dict) or not result.get("run_id"):
                    raise RuntimeError("提交接口未返回 run_id。")
                st.session_state["active_run"] = str(result["run_id"])
                st.success("任务已提交。")
            except RuntimeError as exc:
                st.error(str(exc))
    st.divider()
    st.subheader("当前运行")
    refresh = st.toggle("每 3 秒刷新监控", value=False)
    st.button("立即刷新", key="refresh_monitor")
    if hasattr(st, "fragment"):
        st.fragment(run_every=3 if refresh else None)(monitor)()
    else:
        if refresh:
            st.caption("当前 Streamlit 版本不支持局部定时刷新，请使用立即刷新。")
        monitor()


def report_view() -> None:
    run_id = st.session_state.get("active_run", "")
    st.subheader("📄 可读验证报告")
    st.caption("先看结论和依据，再按需展开代码与原始证据。JSON 仅作为审计和复现格式，不作为主阅读界面。")
    if not run_id:
        st.info("先选择或创建一个运行。")
        return
    run = get_run(run_id)
    if run is None:
        return
    st.caption(f"{run_mode_label(run)} · 模型：{display(run.get('model'))} · 运行 ID：{run_id}")
    try:
        summary = api("GET", run_path(run_id) + "/summary")
    except RuntimeError:
        summary = None
    render_human_report(run, summary if isinstance(summary, dict) else None)
    candidates = records(run.get("candidates"))
    if candidates:
        with st.expander("中间过程：查看生成代码（只读）", expanded=False):
            index = st.selectbox("选择需要查看的候选代码", range(len(candidates)),
                                 format_func=lambda value: display(candidates[value].get("candidate_id")),
                                 key="report_candidate_code")
            selected = candidates[index]
            artifact_id = str(selected.get("artifact_id", ""))
            try:
                detail = api("GET", run_path(run_id) + "/artifacts/" + quote(artifact_id, safe=""))
                if isinstance(detail, dict) and isinstance(detail.get("code"), str):
                    st.caption("只读代码制品 · SHA256：" + display(detail.get("code_sha256")))
                    st.code(detail["code"], language="python", line_numbers=True)
                    st.download_button("下载生成代码", detail["code"], file_name=f"{artifact_id}.py", mime="text/plain")
                else:
                    st.caption("当前候选没有可读取的代码制品。")
            except RuntimeError as exc:
                st.warning(str(exc))

    st.markdown("#### 报告下载")
    col1, col2, col3 = st.columns(3)
    try:
        report = api("GET", run_path(run_id) + "/report")
        col1.download_button("下载审计 JSON", json.dumps(report, ensure_ascii=False, indent=2),
                             file_name="report.json", mime="application/json", help="供程序回放和审计使用")
    except RuntimeError as exc:
        col1.caption(str(exc))
    try:
        content = api("GET", run_path(run_id) + "/report.html", raw=True)
        col2.download_button("下载可打印 HTML 报告", content, file_name="report.html", mime="text/html")
    except RuntimeError as exc:
        col2.caption(str(exc))
    try:
        markdown = api("GET", run_path(run_id) + "/report.md", raw=True)
        col3.download_button("下载 Markdown 报告", markdown, file_name="report.md", mime="text/markdown")
    except RuntimeError as exc:
        col3.caption(str(exc))
    with st.expander("高级：查看原始 JSON 证据", expanded=False):
        try:
            st.json(api("GET", run_path(run_id) + "/report"))
        except RuntimeError as exc:
            st.warning(str(exc))
    st.caption("浏览器界面只显示转义文本，不执行模型代码或直接嵌入后端 HTML。")


def draw_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    """Draw the persisted property graph with type colors and relation labels."""
    try:
        import networkx as nx
        import plotly.graph_objects as go
    except ImportError:
        st.caption("未安装可选绘图库，节点和关系列表仍可完整查看。")
        return
    graph = nx.DiGraph()
    labels = {}
    kinds = {}
    for node in nodes[:120]:
        node_id = node.get("id", node.get("node_id"))
        if node_id is None:
            continue
        node_id = str(node_id)
        graph.add_node(node_id)
        label = node.get("label", node.get("name", node_id))
        kind = str(node.get("kind", "Unknown"))
        kinds[node_id] = kind
        props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
        detail = " · ".join(f"{key}: {display(value)[:100]}" for key, value in list(props.items())[:3])
        labels[node_id] = f"{label}<br><sup>{KIND_LABELS.get(kind, kind)}{(' · ' + detail) if detail else ''}</sup>"
    for edge in edges:
        source = str(edge.get("source", edge.get("source_node_id", "")))
        target = str(edge.get("target", edge.get("target_node_id", "")))
        if source in graph and target in graph:
            graph.add_edge(source, target, relation=edge.get("relation", edge.get("type", "关系")))
    if not graph:
        return
    positions = nx.spring_layout(graph, seed=42)
    edge_x, edge_y = [], []
    edge_labels = []
    for source, target, data in graph.edges(data=True):
        edge_x += [float(positions[source][0]), float(positions[target][0]), None]
        edge_y += [float(positions[source][1]), float(positions[target][1]), None]
        midpoint = ((positions[source][0] + positions[target][0]) / 2, (positions[source][1] + positions[target][1]) / 2)
        edge_labels.append((midpoint, RELATION_LABELS.get(str(data.get("relation")), str(data.get("relation")))))
    traces = [go.Scatter(x=edge_x, y=edge_y, mode="lines", hoverinfo="skip",
                         line={"width": 1.2, "color": "#b4c6cf"}, showlegend=False)]
    for kind in sorted(set(kinds.values()), key=lambda value: KIND_LABELS.get(value, value)):
        selected_nodes = [node for node in graph if kinds.get(node) == kind]
        traces.append(go.Scatter(
            x=[float(positions[node][0]) for node in selected_nodes],
            y=[float(positions[node][1]) for node in selected_nodes], mode="markers",
            name=KIND_LABELS.get(kind, kind), text=[labels[node] for node in selected_nodes], hoverinfo="text",
            marker={"size": 16, "color": KIND_COLORS.get(kind, "#64748b"),
                    "symbol": {"TaskType": "hexagon", "Capability": "circle", "Algorithm": "diamond", "Transform": "square", "DatasetVersion": "triangle-up", "Metric": "star", "Environment": "x", "Source": "circle-open", "Artifact": "square-open", "ValidationRun": "diamond-open", "FailureExperience": "triangle-down"}.get(kind, "circle"),
                    "line": {"width": 1, "color": "white"}},
        ))
    if edge_labels:
        traces.append(go.Scatter(x=[point[0][0] for point in edge_labels], y=[point[0][1] for point in edge_labels], mode="text", text=[point[1] for point in edge_labels], textfont={"size": 9, "color": "#637782"}, hoverinfo="skip", showlegend=False))
    figure = go.Figure(traces)
    figure.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.02}, height=500, margin={"l": 10, "r": 10, "t": 10, "b": 45},
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         xaxis={"visible": False}, yaxis={"visible": False})
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    st.caption("图中每个节点和关系都来自 SQLite property graph；布局仅负责可视化，类型、关系、来源和属性才是可审计事实。最多展示 120 个节点。")


def knowledge_view() -> None:
    st.subheader("🧠 能力知识库与图谱")
    st.caption("这里展示可追溯 property graph：能力、算法、数据、指标、来源、验证运行和失败经验是节点，USES / REQUIRES / EVALUATED_ON 等关系携带明确语义。")
    try:
        payload = api("GET", "/capabilities")
        capabilities = records(payload.get("capabilities")) if isinstance(payload, dict) else []
        if capabilities:
            capability_rows = []
            for item in capabilities:
                capability_rows.append({
                    "能力": item.get("name", item.get("label", item.get("capability_id", "未命名"))),
                    "任务类型": display(item.get("task_types", item.get("task_type"))),
                    "状态": status_label(item.get("status")),
                    "版本": item.get("version", "—"),
                    "来源/证据": len(records(item.get("evidence", item.get("source_ids")))),
                })
            st.dataframe(capability_rows, use_container_width=True, hide_index=True)
            with st.expander("能力卡详情（面向答辩展示）"):
                choice = st.selectbox("选择能力", range(len(capabilities)), format_func=lambda index: capability_rows[index]["能力"], key="capability_detail")
                card = capabilities[choice]
                cols = st.columns(3)
                cols[0].metric("状态", status_label(card.get("status")))
                cols[1].metric("版本", display(card.get("version", "—")))
                cols[2].metric("证据数", len(records(card.get("evidence", card.get("source_ids")))))
                st.markdown(f"**能力摘要**  \n{display(card.get('summary', card.get('description', '未记录')))}")
                st.dataframe([{"前置条件": display(value)} for value in records(card.get("preconditions"))] or [{"前置条件": "未记录"}], use_container_width=True, hide_index=True)
                st.caption("能力卡只描述可复用知识；只有存在匹配验证运行证据时，才会进入 verified 状态。")
        else:
            st.info("尚无能力条目；请先初始化知识库并完成一次运行。")
        graph = api("GET", "/graph")
        nodes = records(graph.get("nodes")) if isinstance(graph, dict) else []
        edges = records(graph.get("edges")) if isinstance(graph, dict) else []
        col1, col2 = st.columns(2)
        col1.metric("节点", len(nodes))
        col2.metric("关系", len(edges))
        draw_graph(nodes, edges)
        if nodes:
            st.markdown("#### 节点邻域与证据")
            node_options = [str(item.get("id")) for item in nodes if item.get("id")]
            selected_node_id = st.selectbox("选择一个节点查看它如何连接", node_options, format_func=lambda node_id: next((f"{item.get('label', node_id)} · {KIND_LABELS.get(item.get('kind', ''), item.get('kind', ''))}" for item in nodes if str(item.get('id')) == node_id), node_id), key="graph_node_detail")
            selected_node = next((item for item in nodes if str(item.get("id")) == selected_node_id), {})
            neighbors = []
            for edge in edges:
                source = str(edge.get("source", edge.get("source_node_id", "")))
                target = str(edge.get("target", edge.get("target_node_id", "")))
                if selected_node_id not in {source, target}:
                    continue
                other = target if source == selected_node_id else source
                other_node = next((item for item in nodes if str(item.get("id")) == other), {})
                neighbors.append({"方向": "出边" if source == selected_node_id else "入边", "关系": RELATION_LABELS.get(str(edge.get("relation", edge.get("type", ""))), edge.get("relation", edge.get("type", "关系"))), "关联节点": other_node.get("label", other), "节点类型": KIND_LABELS.get(other_node.get("kind", ""), other_node.get("kind", "")), "证据": display(edge.get("properties", {}))})
            st.info(f"{selected_node.get('label', selected_node_id)} · {KIND_LABELS.get(selected_node.get('kind', ''), selected_node.get('kind', ''))}")
            st.dataframe(neighbors or [{"方向": "—", "关系": "暂无邻居", "关联节点": "—", "节点类型": "—", "证据": "—"}], use_container_width=True, hide_index=True)
        with st.expander("节点与来源", expanded=False):
            st.dataframe([{ "节点": item.get("label", item.get("id")), "类型": KIND_LABELS.get(item.get("kind", ""), item.get("kind", "")), "属性": display(item.get("properties", {})) } for item in nodes], use_container_width=True, hide_index=True)
        with st.expander("关系、路径与失败经验", expanded=False):
            st.dataframe([{ "起点": item.get("source"), "关系": RELATION_LABELS.get(item.get("relation", ""), item.get("relation", "")), "终点": item.get("target"), "证据属性": display(item.get("properties", {})) } for item in edges], use_container_width=True, hide_index=True)
        st.download_button("导出知识图 JSON", json.dumps(graph, ensure_ascii=False, indent=2),
                           file_name="knowledge_graph.json", mime="application/json")
    except RuntimeError as exc:
        st.error(str(exc))


def history_view() -> None:
    st.subheader("历史记录与资源比较")
    st.caption("真实 API、模拟和回放必须分开统计。跨任务 AP 不直接排名；失败与取消运行保留在分母中。")
    try:
        payload = api("GET", "/runs")
        runs = records(payload.get("runs")) if isinstance(payload, dict) else []
    except RuntimeError as exc:
        st.error(str(exc))
        return
    if not runs:
        st.info("尚无历史运行。")
        return
    modes = sorted({str(item.get("mode", "未记录")) for item in runs})
    allowed = st.multiselect("模式筛选", modes, default=modes)
    selected = [item for item in runs if str(item.get("mode", "未记录")) in allowed]
    summary = []
    for item in selected:
        summary.append({"run_id": item.get("run_id"), "status": item.get("status"),
                        "mode": run_mode_label(item), "dataset_id": item.get("dataset_id"),
                        "created_at": item.get("created_at"), "model": display(item.get("model"))})
    st.dataframe(summary, use_container_width=True, hide_index=True)
    if not selected:
        return
    chosen = st.selectbox("查看历史运行", [str(item["run_id"]) for item in selected if item.get("run_id")])
    if st.button("设为当前运行"):
        st.session_state["active_run"] = chosen
        st.success("已选中。进入“代码与报告”查看该记录；读取历史记录不会重新运行。")
    comparisons = st.multiselect("对比资源（最多 4 个运行）",
                                 [str(item["run_id"]) for item in selected if item.get("run_id")],
                                 max_selections=4)
    if comparisons:
        rows = []
        for run_id in comparisons:
            run = get_run(run_id)
            if run is None:
                continue
            for candidate in candidate_rows(run.get("candidates")):
                rows.append({"run_id": run_id, "mode": run.get("mode"), **candidate})
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("算法训练 CPU 时间/峰值 RSS 与云端 LLM token、请求耗时是不同成本，不能混作 GPU 性能。")


def main() -> None:
    st.set_page_config(page_title="算法能力工厂 · AlgoForge", page_icon="🧩", layout="wide")
    # This literal stylesheet contains no model or user values.
    st.markdown("""<style>
    .stApp{background:linear-gradient(135deg,#f5f8fb 0%,#eef6f5 100%)}.block-container{max-width:1440px;padding-top:1.6rem}
    h1,h2,h3{color:#173b52}.stCaption{color:#5b7180}[data-testid='stMetric']{background:rgba(255,255,255,.9);border:1px solid #d8e5e9;border-radius:12px;padding:13px;box-shadow:0 2px 8px rgba(18,52,70,.04)}
    [data-testid='stSidebar']{background:#eaf2f4}.stButton>button{border-radius:9px;border:1px solid #b8d0d5}.stButton>button[kind='primary']{background:#087f8c;color:white;border:0}
    .hero{background:linear-gradient(120deg,#123c52,#087f8c);color:#fff;border-radius:18px;padding:24px 28px;margin:4px 0 20px;box-shadow:0 10px 28px rgba(8,127,140,.18)}
    .hero h1{color:#fff;margin:0;font-size:2.2rem}.hero p{margin:7px 0 0;color:#d9f4f2;font-size:1rem}.hero-chip{display:inline-block;border:1px solid rgba(255,255,255,.3);border-radius:99px;padding:4px 10px;margin:12px 6px 0 0;font-size:.78rem;color:#e5fffc}
    .stage-track{display:grid;grid-template-columns:repeat(8,minmax(90px,1fr));gap:7px;margin:12px 0 18px}.stage-card{background:rgba(255,255,255,.9);border:1px solid #dce8eb;border-radius:11px;padding:10px 8px;min-height:74px;display:flex;gap:7px;align-items:flex-start}.stage-card small{display:block;color:#70848e;font-size:.69rem;line-height:1.3;margin-top:4px}.stage-icon{font-size:1.2rem;font-weight:700;line-height:1.1}.stage-running{border-color:#f5b84b;box-shadow:0 0 0 2px rgba(245,184,75,.16)}.stage-done{border-color:#9fd3bf}.stage-failed{border-color:#df9696}
    .candidate-card{background:#fff;border:1px solid #d9e6ea;border-radius:13px;padding:15px;min-height:188px;box-shadow:0 3px 12px rgba(18,52,70,.05)}.candidate-top{display:flex;justify-content:space-between;align-items:center}.candidate-algo{color:#087f8c;font-weight:600;margin:12px 0}.badge{font-size:.71rem;border-radius:99px;padding:3px 8px}.badge.good{background:#dcf4e9;color:#13744e}.badge.bad{background:#fde5e5;color:#a63333}.badge.wait{background:#eef2f4;color:#61737d}.candidate-stat{display:flex;justify-content:space-between;border-top:1px solid #edf1f2;padding-top:6px;margin-top:6px;color:#6c7d85;font-size:.78rem}.candidate-stat strong{color:#193f52;font-size:.95rem}
    .info-card{background:#fff;border:1px solid #dce8eb;border-radius:12px;padding:13px 15px;min-height:74px}.info-card b{display:block;color:#173b52}.info-card span{font-size:.8rem;color:#68808a}
    @media(max-width:900px){.stage-track{grid-template-columns:repeat(4,minmax(110px,1fr))}}
    </style>""", unsafe_allow_html=True)
    st.markdown("<div class='hero'><h1>算法能力工厂</h1><p>从自然语言需求到可验证、可追溯、可复现的算法能力</p><span class='hero-chip'>需求理解</span><span class='hero-chip'>知识检索</span><span class='hero-chip'>候选生成</span><span class='hero-chip'>安全验证</span><span class='hero-chip'>经验回写</span></div>", unsafe_allow_html=True)
    with st.sidebar:
        st.subheader("工作台")
        page = st.radio("视图", ["任务与监控", "代码与报告", "知识图谱", "历史与资源"],
                        label_visibility="collapsed")
        st.caption("API 服务")
        st.code(API_URL, language=None)
        with st.expander("连接与环境状态"):
            try:
                health = api("GET", "/health")
                health_cols = st.columns(2)
                health_cols[0].metric("API", "在线" if health.get("status") == "ok" else "异常")
                health_cols[1].metric("并发上限", display(health.get("max_parallel_runs", "—")))
                st.caption(f"默认模型：{display(health.get('model'))} · 约束执行：{display(health.get('sandbox'))}")
                if health.get("local_model_deployed"):
                    st.success("本地模型已连接")
                else:
                    st.info("当前本地 14B 接口状态为未部署；选择 local_http 后可接入兼容服务。")
            except RuntimeError as exc:
                st.error(str(exc))
        with st.form("load_run"):
            run_id = st.text_input("运行 ID", value=st.session_state.get("active_run", ""))
            if st.form_submit_button("打开运行") and run_id.strip():
                st.session_state["active_run"] = run_id.strip()
        st.divider()
        st.markdown("<div class='info-card'><b>推理后端</b><span>DeepSeek API / OpenAI Responses API / 本地 14B HTTP / Mock</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='info-card'><b>4× RTX 4090D 路线</b><span>张量并行或服务副本 · 仅展示配置，不虚构实测</span></div>", unsafe_allow_html=True)
        with st.expander("本地 14B 接入说明"):
            st.code("LOCAL_LLM_BASE_URL=http://127.0.0.1:8001/v1\nLOCAL_LLM_MODEL=your-14b-model\n# provider: local_http", language="bash")
            st.caption("建议使用 vLLM/SGLang 的 OpenAI 兼容服务；4 张 4090D 的显存分配、并行策略与吞吐需要在目标主机实测。")
        st.caption("模型凭证仅由后端读取。UI 不执行生成代码。缺失指标不补零。")
    {"任务与监控": submission_view, "代码与报告": report_view,
     "知识图谱": knowledge_view, "历史与资源": history_view}[page]()


if __name__ == "__main__":
    main()
