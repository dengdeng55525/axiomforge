"""HTTP-contract UI smoke tests; no paid model calls and no code execution."""

from pathlib import Path

import httpx
import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).with_name("app.py")


@pytest.fixture
def backend(monkeypatch):
    calls = []
    report = {
        "run_id": "run-ui", "mode": "mock", "status": "passed",
        "description": "银行营销", "model": "mock", "task_spec": {"dataset_id": "bank"},
        "selected_candidate_id": "c1", "provenance": {"split": "validation"},
        "candidates": [{"candidate_id": "c1", "status": "passed", "artifact_id": "a1",
                        "metrics": {"AP": 0.25}, "checks": {"interface": True},
                        "resources": {"fit_s": 1.5}, "repairs": []}],
        "timing": {"wall_seconds": 12.0}, "usage": None,
    }

    def request(self, method, url, **kwargs):
        del self
        path = httpx.URL(url).path
        calls.append((method, path, kwargs.get("json")))
        payload = {
            "/health": {"status": "ok", "sandbox": "constrained_ast_subprocess"},
            "/runs/run-ui": report,
            "/runs/run-ui/events": {"events": [{"step": "verified", "mode": "mock"}]},
            "/runs/run-ui/artifacts": {"artifacts": [{"artifact_id": "a1"}]},
            "/runs/run-ui/artifacts/a1": {"code": '# <script>alert(1)</script>', "sha256": "abc"},
            "/runs/run-ui/report": report,
            "/capabilities": {"capabilities": [{"id": "cap1", "status": "verified"}]},
            "/graph": {"nodes": [{"id": "n1", "label": "A"}, {"id": "n2", "label": "B"}],
                       "edges": [{"source": "n1", "target": "n2", "type": "USES"}]},
            "/runs": {"runs": [report]},
        }.get(path, {})
        if method == "POST" and path == "/runs":
            payload = {"run_id": "run-ui", "status": "queued"}
        if path.endswith("report.html"):
            return httpx.Response(200, text="<!doctype html><p>Report</p>",
                                  request=httpx.Request(method, url))
        return httpx.Response(200, json=payload, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", request)
    return calls


@pytest.mark.parametrize("view", ["任务与监控", "代码与报告", "知识图谱", "历史与资源"])
def test_all_views_render_from_http_contract(backend, view):
    app = AppTest.from_file(str(APP))
    app.session_state["active_run"] = "run-ui"
    app.run(timeout=15)
    app.sidebar.radio[0].set_value(view).run(timeout=15)
    assert not app.exception
    assert backend
    assert all(path.startswith("/") for _, path, _ in backend)


def test_submission_explicitly_sends_provider_and_constraints(backend):
    app = AppTest.from_file(str(APP)).run(timeout=15)
    provider = next(item for item in app.selectbox if item.label == "LLM 来源")
    provider.set_value("mock")
    submit = next(item for item in app.button if item.label == "提交并开始验证")
    submit.click().run(timeout=15)
    assert not app.exception
    body = next(body for method, path, body in backend if method == "POST" and path == "/runs")
    assert body["provider"] == "mock"
    assert body["dataset_id"] == "bank"
    assert body["max_candidates"] == 2
    assert body["max_repairs"] == 2
    assert body["inject_failure"] is False
    assert app.session_state["active_run"] == "run-ui"
    elapsed = next(item for item in app.metric if item.label == "运行耗时（秒）")
    assert elapsed.value == "12.0"


def test_offline_backend_is_visible_error(monkeypatch):
    def request(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.Client, "request", request)
    app = AppTest.from_file(str(APP)).run(timeout=15)
    assert not app.exception
    assert any("无法读取 API" in error.value for error in app.error)


@pytest.mark.parametrize("provider_id", ["local_http", "openai"])
def test_model_provider_is_an_explicit_http_backend(backend, provider_id):
    """API and local choices share the backend contract without model keys."""
    app = AppTest.from_file(str(APP)).run(timeout=15)
    provider = next(item for item in app.selectbox if item.label == "LLM 来源")
    provider.set_value(provider_id)
    submit = next(item for item in app.button if item.label == "提交并开始验证")
    submit.click().run(timeout=15)
    body = next(body for method, path, body in backend if method == "POST" and path == "/runs")
    assert body["provider"] == provider_id
    assert body["orchestration"] == "multi_role"
    assert body["use_retrieval"] is True
    assert "api_key" not in body
    assert "base_url" not in body
    assert "model" not in body
    assert not app.exception


def test_monitor_renders_stage_timeline_and_missing_metrics_as_dash(backend):
    app = AppTest.from_file(str(APP)).run(timeout=15)
    app.session_state["active_run"] = "run-ui"
    app.sidebar.radio[0].set_value("任务与监控").run(timeout=15)
    assert not app.exception
    # AP is present, while ROC-AUC/lift are absent in the fixture and must not become zero.
    assert any("—" in item.value for item in app.markdown)
    assert any("需求理解" in item.value for item in app.markdown)


@pytest.mark.parametrize("deployment,label", [
    ("official_api", "OpenAI 官方 API · Responses"),
    ("openai_compatible_api", "OpenAI 兼容服务 · Responses"),
])
def test_responses_deployment_label_in_monitor_and_report(backend, monkeypatch, deployment, label):
    request = httpx.Client.request

    def response(self, method, url, **kwargs):
        result = request(self, method, url, **kwargs)
        if httpx.URL(url).path in {"/runs/run-ui", "/runs/run-ui/report"}:
            report = result.json()
            report.update(mode="real", provider="openai", model="gpt-5.5",
                          provider_metadata={"deployment": deployment})
            return httpx.Response(200, json=report, request=result.request)
        return result

    monkeypatch.setattr(httpx.Client, "request", response)
    app = AppTest.from_file(str(APP))
    app.session_state["active_run"] = "run-ui"
    app.run(timeout=15)
    assert not app.exception
    assert any(label in item.value for item in app.info)
    app.sidebar.radio[0].set_value("代码与报告").run(timeout=15)
    assert not app.exception
    assert any(label in item.value for item in app.caption)
