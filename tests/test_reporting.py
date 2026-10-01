"""Evidence-preserving output and model-text escaping for exported reports."""

import copy
import json
from html.parser import HTMLParser

import pytest

from capability_factory.reporting import render_html, render_markdown, write_report


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.extend(attrs)


@pytest.fixture
def report():
    return {
        "run_id": "run-example",
        "status": "completed",
        "mode": "deepseek",
        "description": "银行营销响应预测；禁止通话时长。",
        "task_spec": {"dataset_id": "bank", "split_id": "ordered_60_20_20_v1"},
        "model": "example-model",
        "provenance": {"split": "validation", "source": "UCI"},
        "candidates": [
            {"candidate_id": "candidate-1", "status": "passed",
             "metrics": {"average_precision": 0.1829, "f1": 0.0},
             "checks": {"schema": True}, "resources": {"fit_s": 0.53},
             "repairs": [], "code_sha256": "abc123", "artifact_id": "artifact-1"},
            {"candidate_id": "candidate-2", "status": "failed", "metrics": None},
        ],
        "selected_candidate_id": "candidate-1",
        "events": [{"step": "verified", "role": "evaluator"}],
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "timing": {"elapsed_s": 12.5},
        "knowledge_writeback": {"capability_id": "cap-1", "version": 1},
        "warnings": ["仅验证集结果，未宣称最终测试成绩。"],
    }


def test_html_preserves_measured_values_and_run_identity(report):
    html = render_html(report)
    assert "run-example" in html
    assert "0.1829" in html
    assert "0.0" in html
    assert "真实 LLM" in html
    assert "candidate-2" in html
    assert "failed" in html
    assert html.count('class="selected"') == 1


@pytest.mark.parametrize("field", ["run_id", "description", "model", "status", "mode"])
def test_untrusted_top_level_values_are_escaped(report, field):
    payload = '<script>alert(1)</script><img src=x onerror=alert(2)>'
    report[field] = payload
    html = render_html(report)
    tags = Tags()
    tags.feed(html)
    assert "script" not in tags.tags
    assert "img" not in tags.tags
    assert not any(name.startswith("on") for name, _ in tags.attrs)
    assert "&lt;script&gt;" in html


def test_nested_model_text_and_metric_names_are_escaped(report):
    report["candidates"][0]["plan"] = {"reason": '</pre><script>alert(1)</script>'}
    report["candidates"][0]["metrics"] = {'<img src=x onerror=alert(1)>': 0.125}
    report["events"] = [{"message": '<svg onload=alert(1)>'}]
    html = render_html(report)
    tags = Tags()
    tags.feed(html)
    assert not {"script", "img", "svg"}.intersection(tags.tags)
    assert "0.125" in html
    assert "&lt;svg" in html


def test_empty_report_does_not_invent_success_or_metrics():
    html = render_html({})
    assert "未记录" in html
    assert "模式未记录" in html
    assert "尚无候选验证记录" in html
    assert "average_precision" not in html
    assert "0.0000" not in html
    assert '<td>passed</td>' not in html
    assert 'class="selected"' not in html


def test_null_and_partial_structures_do_not_crash_or_imply_selection():
    html = render_html({
        "mode": None, "task_spec": None, "candidates": [None, {"metrics": None}],
        "selected_candidate_id": None, "usage": None, "events": None,
    })
    assert "未记录" in html
    assert 'class="selected"' not in html


@pytest.mark.parametrize(("mode", "expected"), [
    ("mock", "模拟 LLM"), ("replay", "历史回放"),
    ("unknown-provider", "未识别模式"),
])
def test_mode_never_silently_upgrades_to_real(mode, expected):
    html = render_html({"mode": mode})
    assert expected in html
    assert 'class="badge">真实 LLM' not in html


def test_write_report_preserves_source_and_safe_fixed_paths(report, tmp_path):
    original = copy.deepcopy(report)
    report["run_id"] = "../../outside"
    target = tmp_path / "nested" / "outputs"
    paths = write_report(report, target)
    assert set(paths) == {"json", "html", "markdown"}
    assert (target / "report.json").is_file()
    assert (target / "report.html").is_file()
    assert (target / "report.md").is_file()
    assert json.loads((target / "report.json").read_text()) == report
    assert not (tmp_path / "outside").exists()
    report["run_id"] = original["run_id"]
    assert report == original


def test_nonfinite_observations_are_json_null_not_zero(tmp_path):
    report = {"candidates": [{"metrics": {"AP": float("nan"), "ROC_AUC": float("inf")}}]}
    write_report(report, tmp_path)
    saved = json.loads((tmp_path / "report.json").read_text())
    assert saved["candidates"][0]["metrics"] == {"AP": None, "ROC_AUC": None}


def test_markdown_fence_cannot_be_closed_by_model_text():
    result = render_markdown({"description": '`````\n<script>alert(1)</script>\n`````'})
    lines = result.splitlines()
    assert "``````json" in lines
    start = lines.index("``````json")
    assert "``````" in lines[start + 1 :]
    assert lines[-1] == "</details>"


def test_html_is_self_contained_and_has_restrictive_policy(report):
    html = render_html(report)
    tags = Tags()
    tags.feed(html)
    assert "Content-Security-Policy" in html
    assert "default-src 'none'" in html
    assert "script" not in tags.tags
    assert "link" not in tags.tags
