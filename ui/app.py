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
    st.subheader("可追溯步骤")
    try:
        payload = api("GET", run_path(run_id) + "/events")
        events = records(payload.get("events")) if isinstance(payload, dict) else []
        if events:
            st.dataframe([{key: display(value) for key, value in event.items()}
                          for event in events], use_container_width=True, hide_index=True)
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
        provider = col1.selectbox("LLM 来源", ["deepseek", "mock"],
                                  format_func=lambda value: "DeepSeek 真实 API" if value == "deepseek"
                                  else "Mock 模拟（标记展示）")
        search = col2.selectbox("候选搜索", ["compare", "beam"],
                                format_func=lambda value: "并列候选比较" if value == "compare"
                                else "Beam Search")
        candidates = col3.selectbox("候选上限", [2, 6], index=0)
        with st.expander("修复、知识与演示设置"):
            max_repairs = st.slider("每候选最多修复次数", 0, 2, 2)
            use_graph = st.checkbox("使用知识图谱证据检索", value=True)
            inject_failure = st.checkbox("注入标记故障（仅用于修复演示）", value=False)
            st.caption("故障注入结果应与自然错误分开统计。候选数是上限，失败或预算耗尽可能提前停止。")
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
    .stApp{background:#f6f9fc}.block-container{max-width:1320px;padding-top:2.1rem}
    h1,h2,h3{color:#18364a}[data-testid='stMetric']{background:white;border:1px solid #dce6ed;
    border-radius:10px;padding:13px}[data-testid='stSidebar']{background:#eef4f7}
    .stButton>button{border-radius:8px}section[data-testid='stSidebar'] small{color:#526578}
    </style>""", unsafe_allow_html=True)
    st.title("算法能力工厂")
    st.caption("理解需求 → 检索证据 → 生成候选 → 统一验证 → 有限修复 → 知识沉淀")
    with st.sidebar:
        st.subheader("工作台")
        page = st.radio("视图", ["任务与监控", "代码与报告", "知识图谱", "历史与资源"],
                        label_visibility="collapsed")
        st.caption("API 服务")
        st.code(API_URL, language=None)
        with st.expander("连接与环境状态"):
            try:
                health = api("GET", "/health")
                st.json(health)
            except RuntimeError as exc:
                st.error(str(exc))
        with st.form("load_run"):
            run_id = st.text_input("运行 ID", value=st.session_state.get("active_run", ""))
            if st.form_submit_button("打开运行") and run_id.strip():
                st.session_state["active_run"] = run_id.strip()
        st.divider()
        st.caption("模型凭证仅由后端读取。UI 不执行生成代码。缺失指标不补零。")
        st.caption("API 优先完成当前项目；1–6 卡本地推理是后续兼容路径，未实测不展示加速结论。")
    {"任务与监控": submission_view, "代码与报告": report_view,
     "知识图谱": knowledge_view, "历史与资源": history_view}[page]()


if __name__ == "__main__":
    main()
