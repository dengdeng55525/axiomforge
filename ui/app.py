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
    "real": "真实 LLM 调用",
    "api": "真实 LLM / API",
    "mock": "模拟 LLM / 仅验证工程流程",
    "replay": "历史回放 / 非当前实时执行",
}
PROVIDER_LABELS = {
    "deepseek": "DeepSeek V4.1 API",
    "local_http": "本地 14B · OpenAI 兼容接口",
    "mock": "Mock · 离线演示",
}
STAGE_DEFINITIONS = [
    ("interpret", "需求理解", "把自然语言约束转成可验证任务"),
    ("retrieve", "证据检索", "从知识库与图谱召回依据"),
    ("plan", "候选规划", "生成可比较的算法方案"),
    ("generate", "代码生成", "按受限语法生成候选 Pipeline"),
    ("validate", "独立验证", "隔离进程训练并计算指标"),
    ("repair", "有限修复", "根据失败证据修复，最多两轮"),
    ("writeback", "经验沉淀", "写入版本化能力与失败经验"),
    ("report", "报告交付", "汇总证据、资源与可复现制品"),
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
        st.info("候选尚未生成，验证完成后会在这里显示对比卡片。")
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


def show_identity(run: dict[str, Any]) -> None:
    st.info(mode_label(run.get("mode")))
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
        st.json(run["warnings"])
    rows = candidate_rows(run.get("candidates"))
    if rows:
        st.subheader("候选验证进度")
        st.dataframe(rows, use_container_width=True, hide_index=True)
        render_candidate_cards(records(run.get("candidates")), run.get("selected_candidate_id"))
        render_metric_chart(records(run.get("candidates")))
        with st.expander("训练资源与 LLM 预算", expanded=False):
            render_resources(run)
    st.subheader("可追溯步骤")
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
        provider = col1.selectbox("LLM 来源", ["deepseek", "local_http", "mock"],
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
    st.subheader("候选、代码与验证报告")
    if not run_id:
        st.info("先选择或创建一个运行。")
        return
    run = get_run(run_id)
    if run is None:
        return
    show_identity(run)
    rows = candidate_rows(run.get("candidates"))
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        render_candidate_cards(records(run.get("candidates")), run.get("selected_candidate_id"))
        render_metric_chart(records(run.get("candidates")))
    st.caption("缺失值保留为空，不代表零分或通过。仅同一数据、切分与指标定义下的候选适合比较。")
    candidates = records(run.get("candidates"))
    if candidates:
        index = st.selectbox("检查候选", range(len(candidates)),
                             format_func=lambda value: display(candidates[value].get("candidate_id")))
        selected = candidates[index]
        for key, label in [("plan", "规划与证据"), ("checks", "功能、接口与稳定性检查"),
                           ("repairs", "修复轨迹"), ("resources", "资源观测")]:
            with st.expander(label, expanded=key == "checks"):
                st.json(selected.get(key))
    try:
        payload = api("GET", run_path(run_id) + "/artifacts")
        artifacts = records(payload.get("artifacts")) if isinstance(payload, dict) else []
        if artifacts:
            choice = st.selectbox("代码制品（只读）", range(len(artifacts)),
                                  format_func=lambda value: display(artifacts[value].get("artifact_id")))
            artifact_id = str(artifacts[choice].get("artifact_id", ""))
            detail = api("GET", run_path(run_id) + "/artifacts/" + quote(artifact_id, safe=""))
            if isinstance(detail, dict):
                st.caption("制品哈希：" + display(detail.get("code_sha256", detail.get("sha256"))))
                code = detail.get("code", detail.get("source"))
                if isinstance(code, str):
                    st.code(code, language="python", line_numbers=True)
                    st.download_button("下载代码文本", code, file_name="model.py", mime="text/plain")
                else:
                    st.json(detail)
        else:
            st.caption("尚无可读取代码制品。")
    except RuntimeError as exc:
        st.warning(str(exc))
    col1, col2 = st.columns(2)
    try:
        report = api("GET", run_path(run_id) + "/report")
        col1.download_button("下载 JSON 原始报告", json.dumps(report, ensure_ascii=False, indent=2),
                             file_name="report.json", mime="application/json")
        with st.expander("完整原始报告"):
            st.json(report)
    except RuntimeError as exc:
        col1.caption(str(exc))
    try:
        content = api("GET", run_path(run_id) + "/report.html", raw=True)
        col2.download_button("下载离线 HTML 报告", content, file_name="report.html", mime="text/html")
    except RuntimeError as exc:
        col2.caption(str(exc))
    st.caption("浏览器界面只显示转义文本，不执行模型代码或直接嵌入后端 HTML。")


def draw_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    """Draw a bounded local graph; facts remain available in the tables below."""
    try:
        import networkx as nx
        import plotly.graph_objects as go
    except ImportError:
        st.caption("未安装可选绘图库，节点和关系列表仍可完整查看。")
        return
    graph = nx.DiGraph()
    labels = {}
    for node in nodes[:120]:
        node_id = node.get("id", node.get("node_id"))
        if node_id is None:
            continue
        node_id = str(node_id)
        graph.add_node(node_id)
        label = node.get("label", node.get("name", node_id))
        labels[node_id] = html.escape(str(label), quote=True)
    for edge in edges:
        source = str(edge.get("source", edge.get("source_node_id", "")))
        target = str(edge.get("target", edge.get("target_node_id", "")))
        if source in graph and target in graph:
            graph.add_edge(source, target)
    if not graph:
        return
    positions = nx.spring_layout(graph, seed=42)
    edge_x, edge_y = [], []
    for source, target in graph.edges:
        edge_x += [float(positions[source][0]), float(positions[target][0]), None]
        edge_y += [float(positions[source][1]), float(positions[target][1]), None]
    figure = go.Figure([
        go.Scatter(x=edge_x, y=edge_y, mode="lines", hoverinfo="skip",
                   line={"width": 1, "color": "#a9bac6"}),
        go.Scatter(x=[float(positions[node][0]) for node in graph],
                   y=[float(positions[node][1]) for node in graph], mode="markers",
                   text=[labels[node] for node in graph], hoverinfo="text",
                   marker={"size": 13, "color": "#087f8c", "line": {"width": 1, "color": "white"}}),
    ])
    figure.update_layout(showlegend=False, height=390, margin={"l": 10, "r": 10, "t": 10, "b": 10},
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         xaxis={"visible": False}, yaxis={"visible": False})
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    st.caption("布局只显示前 120 个节点；有向关系、类型与证据以完整边表为准。无外部 CDN 请求。")


def knowledge_view() -> None:
    st.subheader("可追溯能力与知识图谱")
    st.caption("能力数量不是效果指标：查看出处、适用约束、验证状态和回写运行，确认知识确实影响生成。")
    try:
        payload = api("GET", "/capabilities")
        capabilities = records(payload.get("capabilities")) if isinstance(payload, dict) else []
        if capabilities:
            st.dataframe([{key: display(value) for key, value in item.items()}
                          for item in capabilities], use_container_width=True, hide_index=True)
            with st.expander("能力版本完整记录"):
                st.json(capabilities)
        else:
            st.info("尚无能力条目；请先初始化知识库并完成一次运行。")
        graph = api("GET", "/graph")
        nodes = records(graph.get("nodes")) if isinstance(graph, dict) else []
        edges = records(graph.get("edges")) if isinstance(graph, dict) else []
        col1, col2 = st.columns(2)
        col1.metric("节点", len(nodes))
        col2.metric("关系", len(edges))
        draw_graph(nodes, edges)
        with st.expander("节点与来源", expanded=False):
            st.dataframe([{key: display(value) for key, value in item.items()}
                          for item in nodes], use_container_width=True, hide_index=True)
        with st.expander("关系、路径与失败经验", expanded=False):
            st.dataframe([{key: display(value) for key, value in item.items()}
                          for item in edges], use_container_width=True, hide_index=True)
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
                        "mode": item.get("mode"), "dataset_id": item.get("dataset_id"),
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
                    st.info("本地 14B 接口尚未部署，选择 local_http 后可直接接入兼容服务。")
            except RuntimeError as exc:
                st.error(str(exc))
        with st.form("load_run"):
            run_id = st.text_input("运行 ID", value=st.session_state.get("active_run", ""))
            if st.form_submit_button("打开运行") and run_id.strip():
                st.session_state["active_run"] = run_id.strip()
        st.divider()
        st.markdown("<div class='info-card'><b>推理后端</b><span>DeepSeek V4.1 API / 本地 14B HTTP</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='info-card'><b>4× RTX 4090D 路线</b><span>张量并行或服务副本 · 仅展示配置，不虚构实测</span></div>", unsafe_allow_html=True)
        with st.expander("本地 14B 接入说明"):
            st.code("LOCAL_LLM_BASE_URL=http://127.0.0.1:8001/v1\nLOCAL_LLM_MODEL=your-14b-model\n# provider: local_http", language="bash")
            st.caption("建议使用 vLLM/SGLang 的 OpenAI 兼容服务；4 张 4090D 的显存分配、并行策略与吞吐需要在目标主机实测。")
        st.caption("模型凭证仅由后端读取。UI 不执行生成代码。缺失指标不补零。")
    {"任务与监控": submission_view, "代码与报告": report_view,
     "知识图谱": knowledge_view, "历史与资源": history_view}[page]()


if __name__ == "__main__":
    main()
