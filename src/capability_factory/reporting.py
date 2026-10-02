"""Render auditable reports without executing or trusting model-authored markup.

Only observations supplied by the service are rendered. Missing metrics stay missing;
the presentation layer must never manufacture a score, success status, or baseline.
"""

from __future__ import annotations

import html
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

MODE_LABELS = {
    "deepseek": "真实 LLM · DeepSeek API",
    "real": "真实 LLM 调用",
    "api": "真实 LLM · 外部 API",
    "mock": "模拟 LLM · 流程验证模式",
    "replay": "历史回放 · 固定记录",
}

_CSS = """
:root{color-scheme:light;--ink:#183047;--muted:#526578;--line:#dbe4ec;
--accent:#076d77;--paper:#fff;--wash:#f3f7fa}
*{box-sizing:border-box}body{margin:0;background:var(--wash);color:var(--ink);
font:15px/1.65 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
main{max-width:1180px;margin:32px auto;padding:0 24px 48px}
header{background:#16364b;color:white;padding:30px 32px;border-radius:14px}
header h1{font-size:28px;margin:8px 0}header p{color:#d9e9f0;margin:8px 0}
.eyebrow{text-transform:uppercase;font-size:12px;letter-spacing:.13em}
.badge{display:inline-block;background:#e8f7f3;color:#125247;padding:4px 10px;
border-radius:6px;font-weight:650;max-width:100%;overflow-wrap:anywhere}
section{background:var(--paper);padding:24px 28px;margin:18px 0;border:1px solid
var(--line);border-radius:12px}h2{font-size:20px;margin:0 0 14px}
h3{font-size:16px;margin:22px 0 8px}.muted,footer{color:var(--muted)}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:10px;text-align:left;
vertical-align:top;overflow-wrap:anywhere}th{background:#eef4f7}tr.selected{background:#edf9f5}
pre{background:#f4f7fa;border:1px solid var(--line);padding:15px;border-radius:7px;
white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.6 ui-monospace,monospace}
dl{display:grid;grid-template-columns:minmax(130px,1fr) 3fr;gap:7px 20px}
dt{font-weight:650}dd{margin:0;overflow-wrap:anywhere}.warning{border-left:4px solid #b77c20}
details{padding:10px 0;border-top:1px solid var(--line)}summary{cursor:pointer;font-weight:650}
footer{font-size:12px;padding-top:10px}@media print{body{background:white}main{margin:0;
max-width:none;padding:0}section{break-inside:avoid}details{display:block}}
@media(max-width:640px){main{padding:0 12px}header,section{padding:20px}dl{grid-template-columns:1fr}}
"""


def _clean(value: Any) -> Any:
    """Make JSON portable, representing non-finite observations as missing."""
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _json(value: Any) -> str:
    return json.dumps(_clean(value), ensure_ascii=False, indent=2, allow_nan=False)


def _display(value: Any) -> str:
    if value is None or value == "":
        return "未记录"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (dict, list, tuple)):
        return _json(value)
    return str(value)


def _escape(value: Any) -> str:
    return html.escape(_display(value), quote=True)


def _pre(value: Any) -> str:
    if value is None:
        return '<p class="muted">未记录</p>'
    return f"<pre>{html.escape(_json(value), quote=True)}</pre>"


def _mode(report: Mapping[str, Any]) -> str:
    mode = report.get("mode")
    if mode is None:
        return "模式未记录 · 不推断真实调用"
    if mode == "real" and report.get("provider") == "openai":
        deployment = _mapping(report.get("provider_metadata")).get("deployment")
        service = {"official_api": "OpenAI 官方 API", "openai_compatible_api": "OpenAI 兼容服务"}.get(
            deployment, "OpenAI Responses API",
        )
        return f"真实 LLM · {service} · Responses"
    return MODE_LABELS.get(str(mode).lower(), f"未识别模式：{mode}")


def _definition_list(values: Mapping[str, Any]) -> str:
    return "<dl>" + "".join(
        f"<dt>{_escape(key)}</dt><dd>{_escape(value)}</dd>"
        for key, value in values.items()
    ) + "</dl>"


def _candidate_table(candidates: list[Any], selected: Any) -> str:
    items = [_mapping(item) for item in candidates]
    if not items:
        return '<p class="muted">尚无候选验证记录。</p>'
    metric_keys = sorted({str(key) for item in items for key in _mapping(item.get("metrics"))})
    headers = ["候选 ID", "状态", "质量门槛", "选中", *metric_keys]
    header = "".join(f"<th>{_escape(name)}</th>" for name in headers)
    rows = []
    for item in items:
        candidate_id = item.get("candidate_id")
        chosen = candidate_id is not None and selected is not None and candidate_id == selected
        metrics = _mapping(item.get("metrics"))
        values = [candidate_id, item.get("status"), item.get("quality_status"),
                  "是" if chosen else "—"]
        values += [metrics.get(key) for key in metric_keys]
        css = ' class="selected"' if chosen else ""
        rows.append(f"<tr{css}>" + "".join(f"<td>{_escape(v)}</td>" for v in values) + "</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>' + header
        + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def render_html(report: dict[str, Any]) -> str:
    """Return a standalone HTML report; all dynamic values are escaped."""
    data = _mapping(_clean(report))
    run_id = data.get("run_id")
    candidates = _sequence(data.get("candidates"))
    body = [
        '<header><div class="eyebrow">AXIOMFORGE · 知衡</div>',
        "<h1>算法能力验证报告</h1>",
        f'<span class="badge">{_escape(_mode(data))}</span>',
        f"<p>运行 ID：{_escape(run_id)}</p></header>",
        "<section><h2>运行概览</h2>",
        _definition_list({
            "运行状态": data.get("status"),
            "质量门槛": data.get("quality_status"),
            "模型与版本": data.get("model"),
            "选中候选": data.get("selected_candidate_id"),
        }),
        '<p class="muted">指标仅来自提供的验证记录。未记录项目显示为缺失，质量、安全和泛化能力分别查看对应检查与评估结果。</p></section>',
        "<section><h2>需求与约束</h2>",
        f"<p>{_escape(data.get('description'))}</p>",
        _pre(data.get("task_spec")),
        "</section><section><h2>数据、证据与来源</h2>",
        _pre(data.get("provenance")),
        "</section><section><h2>验证结果与候选比较</h2>",
        _candidate_table(candidates, data.get("selected_candidate_id")),
        '<p class="muted">仅同一任务、切分和预算下的指标适合直接比较。AP 指 average precision；'
        '候选选择依据验证集结果，最终测试集结果请结合 provenance 单独查看。</p>',
    ]
    for value in candidates:
        item = _mapping(value)
        body += [
            f"<h3>候选 {_escape(item.get('candidate_id'))}</h3>",
            _definition_list({
                "状态": item.get("status"),
                "制品 ID": item.get("artifact_id"),
                "代码 SHA256": item.get("code_sha256"),
            }),
        ]
        for key, title in (
            ("plan", "计划与依据"), ("checks", "验证检查"),
            ("resources", "资源观测"), ("repairs", "修复记录"),
        ):
            body.append(f"<details><summary>{title}</summary>{_pre(item.get(key))}</details>")
        extra = {key: value for key, value in item.items() if key not in {
            "candidate_id", "status", "artifact_id", "code_sha256", "plan",
            "metrics", "checks", "resources", "repairs",
        }}
        if extra:
            body.append("<details><summary>其他候选事实</summary>" + _pre(extra) + "</details>")
    optimization = _mapping(data.get("optimization"))
    if optimization:
        body += ["</section><section><h2>质量与资源权衡</h2>",
                 "<p>在已通过验证且测量齐全的候选中，同时比较 AP（越高越好）、训练耗时和峰值 RSS（越低越好）。</p>",
                 _definition_list({"Pareto 前沿候选": optimization.get("frontier_candidate_ids"),
                                   "观测次数": optimization.get("measurement_repetitions")}),
                 '<div class="table-wrap"><table><thead><tr><th>候选</th><th>AP</th><th>训练秒数</th><th>峰值 RSS MiB</th><th>前沿</th></tr></thead><tbody>']
        for row in _sequence(optimization.get("candidates")):
            body.append("<tr>" + "".join(f"<td>{_escape(row.get(key))}</td>" for key in
                        ("candidate_id", "average_precision", "fit_seconds", "peak_rss_mib", "pareto_optimal")) + "</tr>")
        body += ["</tbody></table></div>",
                 "<p>单次资源观测不证明稳定加速；候选选择仍以验证 AP 为主。</p>",
                 "<details><summary>父子方案变化与分析审计</summary>", _pre(optimization), "</details>"]
    body += ["</section><section><h2>资源、调用与耗时</h2>",
             "<h3>LLM 用量</h3>", _pre(data.get("usage")),
             "<h3>计时记录</h3>", _pre(data.get("timing")),
             "</section><section><h2>知识回写</h2>", _pre(data.get("knowledge_writeback")),
             '</section><section class="warning"><h2>警告与局限</h2>',
             _pre(data.get("warnings")),
             '<p class="muted">mock 仅验证流程；replay 仅呈现历史记录。'
             '多卡配置提供接入规划；多卡部署结论以目标环境实测制品与验证证据为准。</p>',
             "</section><section><h2>事件与复现证据</h2>", _pre(data.get("events")),
             "</section><section><details><summary>完整原始报告</summary>",
             _pre(data), "</details></section>",
             "<footer>本报告离线可读，不加载外部脚本、字体或 CDN。模型文本不会作为 HTML 执行。</footer>"]
    title = html.escape(f"AxiomForge · 知衡 · 算法能力验证报告 · {_display(run_id)}", quote=True)
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" '
        """content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'">"""
        f"<title>{title}</title><style>{_CSS}</style></head><body><main>"
        + "".join(body) + "</main></body></html>"
    )


def _md(value: Any) -> str:
    """Keep model-authored strings as inline text, including in table cells."""
    text = html.escape(_display(value), quote=True)
    text = re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)
    return text.replace("\r", " ").replace("\n", " ")


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(_md(v) for v in headers) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
    lines += ["| " + " | ".join(_md(v) for v in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def _audit_details(title: str, value: Any) -> str:
    # JSON remains lossless inside a fence longer than any model-authored run
    # of backticks. Never put model text in an HTML summary or attribute.
    raw = _json(value)
    longest = max((len(match) for match in re.findall(r"`+", raw)), default=0)
    fence = "`" * max(4, longest + 1)
    return (f"<details>\n<summary>{html.escape(title)}</summary>\n\n"
            f"{fence}json\n{raw}\n{fence}\n\n</details>\n")


def render_markdown(report: dict[str, Any]) -> str:
    """Render decisions and measured evidence first; fold detailed audit JSON.

    Displayed values all come from the supplied report. No LLM, filesystem read,
    scoring or selection is performed here, and the original object is untouched.
    """
    data = _mapping(_clean(report))
    candidates = [_mapping(item) for item in _sequence(data.get("candidates"))
                  if isinstance(item, Mapping)]
    selected_id = data.get("selected_candidate_id")
    selected = next((item for item in candidates if selected_id is not None
                     and item.get("candidate_id") == selected_id), {})
    metrics = _mapping(selected.get("metrics"))
    task = _mapping(data.get("task_spec"))
    dataset = _mapping(_mapping(data.get("provenance")).get("dataset"))
    usage, timing = _mapping(data.get("usage")), _mapping(data.get("timing"))
    sections = ["# 算法能力验证报告\n", "AxiomForge · 知衡\n", "## 运行结论\n",
                _md_table(["项目", "记录"], [
                    ["运行 ID", data.get("run_id")], ["状态", data.get("status")],
                    ["运行模式", _mode(data)], ["模型", data.get("model")],
                    ["数据集", data.get("dataset_id", task.get("dataset_id"))],
                    ["选中候选", selected_id],
                    ["质量状态", selected.get("quality_status", data.get("quality_status"))],
                ])]
    if data.get("failure_reason"):
        sections.append("运行诊断：" + _md(data["failure_reason"]) + "\n")
    if selected:
        sections.append(_md_table(["选中候选指标", "观测值"], [
            ["Average Precision (AP)", metrics.get("average_precision")],
            ["Dummy AP", metrics.get("dummy_average_precision")],
            ["AP 较基线提升", metrics.get("ap_improvement_over_dummy")],
            ["ROC-AUC", metrics.get("roc_auc")],
            ["F1 @ 0.5", metrics.get("f1_threshold_0_5")],
            ["Lift @ 10%", metrics.get("lift_at_10pct")],
        ]))
    else:
        sections.append("当前报告未记录可定位的选中候选。\n")
    sections += ["指标来自报告记录的评估范围；缺失项显示为未记录。Mock 表示模拟模型调用，"
                 "replay 表示历史回放。功能检查、指标质量和业务上线评估分别复核。\n",
                 "## 需求与数据协议\n", _md(data.get("description")) + "\n",
                 _md_table(["协议", "记录"], [
                     ["任务类型", task.get("task_type")], ["划分策略", dataset.get("split_policy")],
                     ["特征策略", dataset.get("feature_policy", task.get("feature_policy"))],
                     ["训练样本", dataset.get("train_rows")],
                     ["验证样本", dataset.get("validation_rows")],
                     ["封存测试集已评分", dataset.get("sealed_test_scored",
                         _mapping(data.get("provenance")).get("sealed_test_scored"))],
                     ["原始数据 SHA256", dataset.get("raw_sha256")],
                 ]), "## 候选方案比较\n"]
    if candidates:
        rows = []
        for candidate in candidates:
            plan, score = _mapping(candidate.get("plan")), _mapping(candidate.get("metrics"))
            resources = _mapping(candidate.get("resources"))
            rows.append([candidate.get("candidate_id"), plan.get("algorithm"),
                         candidate.get("status"), score.get("average_precision"),
                         score.get("dummy_average_precision"), score.get("roc_auc"),
                         resources.get("fit_seconds"), resources.get("peak_rss_mib")])
        sections.append(_md_table(["候选", "算法", "状态", "AP", "Dummy AP", "ROC-AUC",
                                   "训练秒数", "峰值 RSS MiB"], rows))
    else:
        sections.append("尚无候选验证记录。\n")
    sections.append("## 验证证据与设计依据\n")
    for candidate in candidates:
        plan = _mapping(candidate.get("plan"))
        sections += ["### " + _md(candidate.get("candidate_id")) + "\n",
                     "设计依据：" + _md(plan.get("rationale")) + "\n",
                     "引用能力：" + _md(plan.get("evidence_ids")) + "\n",
                     "代码 SHA256：" + _md(candidate.get("code_sha256")) + "\n"]
        checks = [c for c in _sequence(candidate.get("checks")) if isinstance(c, Mapping)]
        if checks:
            sections.append(_md_table(["检查", "结果", "必需", "证据"], [
                [check.get("name"), {True: "通过", False: "失败"}.get(check.get("passed"), "未记录"),
                 check.get("mandatory"), check.get("detail")] for check in checks]))
        else:
            sections.append("尚无逐项检查记录。\n")
        sections.append(_audit_details("修复与执行尝试", {
            "attempts": candidate.get("attempts"), "repairs": candidate.get("repairs"),
            "error": candidate.get("error"),
        }))
    sections += ["## 资源与知识沉淀\n", _md_table(["项目", "记录"], [
        ["模型调用数", usage.get("calls")], ["输入 token", usage.get("input_tokens")],
        ["输出 token", usage.get("output_tokens")], ["运行耗时（秒）", timing.get("wall_seconds")],
        ["时限（秒）", timing.get("budget_seconds")],
        ["运行已保存", _mapping(data.get("knowledge_writeback")).get("run_saved")],
    ]), _audit_details("知识依据、图谱回写与 Agent 时间线", {
        "evidence": data.get("evidence"), "knowledge_writeback": data.get("knowledge_writeback"),
        "events": data.get("events"), "search_tree": data.get("search_tree"),
    }), "## 模型总结与运行提示\n",
        "模型总结：" + _md(_mapping(data.get("explanation")).get("summary")) + "\n"]
    notes = (_sequence(data.get("warnings"))
             + _sequence(_mapping(data.get("explanation")).get("limitations")))
    sections.append("\n".join("- " + _md(item) for item in notes) + "\n"
                    if notes else "未记录额外运行提示。\n")
    sections.append(_audit_details("完整 JSON 审计记录", data))
    return "\n".join(sections)


def write_report(report: dict[str, Any], directory: Path) -> dict[str, str]:
    """Write JSON, standalone HTML and Markdown using fixed local filenames."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    data = _mapping(_clean(report))
    outputs = {
        "json": (target / "report.json", _json(data) + "\n"),
        "html": (target / "report.html", render_html(data)),
        "markdown": (target / "report.md", render_markdown(data)),
    }
    paths = {}
    for kind, (path, content) in outputs.items():
        path.write_text(content, encoding="utf-8")
        paths[kind] = str(path)
    return paths
