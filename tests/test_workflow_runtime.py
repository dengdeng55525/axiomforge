"""Real-data mock integration and persistent failure-state checks; no API costs."""

import json
import threading
from pathlib import Path

import pytest

from capability_factory.contracts import RunRequest
from capability_factory.knowledge import KnowledgeStore
from capability_factory.providers import MockProvider, ProviderError
from capability_factory.settings import Settings
from capability_factory.workflow import Workflow

PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings(tmp_path):
    if not (PROJECT / "data/raw/bank-additional-full.csv").exists():
        pytest.skip("Run scripts/verify_data.py for real-data integration fixtures")
    for directory in ["data", "docs", "configs"]:
        (tmp_path / directory).symlink_to(PROJECT / directory, target_is_directory=True)
    return Settings(root=tmp_path)


@pytest.mark.integration
def test_mock_repair_is_real_revalidation_and_memory_writeback(settings):
    report = Workflow(settings).run(RunRequest(description="通话前银行预测，比较验证并保存失败经验", provider="mock", max_candidates=1, inject_failure=True))
    assert report["status"] == "passed"
    candidate = report["candidates"][0]
    assert [attempt["status"] for attempt in candidate["attempts"]] == ["failed", "passed"]
    assert candidate["attempts"][0]["code_sha256"] != candidate["attempts"][1]["code_sha256"]
    assert candidate["metrics"]["average_precision"] > candidate["metrics"]["dummy_average_precision"]
    assert report["mode"] == "mock"
    assert report["provenance"]["sealed_test_scored"] is False
    assert report["knowledge_writeback"]["experiences"]
    assert Path(report["report_paths"]["html"]).exists()


@pytest.mark.integration
def test_sms_mock_beam_uses_legal_variants(settings):
    report = Workflow(settings).run(RunRequest(description="比较短信垃圾分类候选并搜索适用参数", provider="mock", dataset_id="sms", max_candidates=6, search="beam"))
    assert report["status"] == "passed", report.get("failure_reason")
    assert 2 < len(report["candidates"]) <= 6
    assert any(node["parent_id"] for node in report["search_tree"])
    assert any(node["pruned"] for node in report["search_tree"])
    assert all(item["plan"]["variant"] != "balanced" for item in report["candidates"] if item["plan"]["algorithm"] == "nb")


def test_early_cancellation_persists_terminal_status(settings):
    cancellation = threading.Event()
    cancellation.set()
    report = Workflow(settings).run(RunRequest(description="此任务应当在生成之前取消", provider="mock"), cancel=cancellation)
    assert report["status"] == "cancelled"
    assert not report["candidates"]
    assert report["usage"]["calls"] == 0


def test_missing_key_fails_without_mock_fallback(settings):
    report = Workflow(settings).run(RunRequest(description="真实API没有密钥时必须明确失败", provider="deepseek"))
    assert report["status"] == "failed"
    assert report["mode"] == "real"
    assert not report["candidates"]
    assert "missing" in report["failure_reason"]


def test_run_id_traversal_rejected(settings):
    with pytest.raises(ValueError, match="run_id"):
        Workflow(settings).run(RunRequest(description="路径验证测试", provider="mock"), run_id="../escape")


@pytest.mark.integration
def test_single_shot_has_no_hidden_roles_or_retrieval(settings):
    report = Workflow(settings).run(RunRequest(description="生成短信分类用于消融实验", provider="mock", dataset_id="sms",
                                              max_candidates=1, max_repairs=0, orchestration="single_shot", use_retrieval=False))
    assert report["status"] == "passed"
    assert report["usage"]["calls"] == 1
    assert report["evidence"] == []
    persisted = KnowledgeStore(settings.db_path).get_run(report["run_id"])
    assert persisted["status"] == "passed"
    assert json.loads(Path(report["report_paths"]["json"]).read_text())["mode"] == "mock"


def test_only_immediately_successful_repair_becomes_verified_memory(settings, monkeypatch):
    outcomes = iter([
        {"status": "failed", "error": {"type": "FirstFault", "message": "first", "repairable": True}},
        {"status": "failed", "error": {"type": "SecondFault", "message": "second", "repairable": True}},
        {"status": "passed", "metrics": {"average_precision": 0.5}},
    ])
    monkeypatch.setattr("capability_factory.execution.validate_candidate", lambda *args, **kwargs: next(outcomes))
    report = Workflow(settings).run(RunRequest(description="验证每一步修复的证据绑定", provider="mock", max_candidates=1))
    assert report["status"] == "passed", report.get("failure_reason")
    memories = report["knowledge_writeback"]["experiences"]
    assert {item["error_type"]: item["validated"] for item in memories} == {"FirstFault": False, "SecondFault": True}


def test_cancel_preserves_returned_worker_termination_evidence(settings, monkeypatch):
    cancellation = threading.Event()

    def validate(*args, **kwargs):
        cancellation.set()
        return {"status": "cancelled", "resources": {"worker_pid": 12345, "terminated": True},
                "error": {"type": "cancelled", "message": "worker terminated", "repairable": False}}

    monkeypatch.setattr("capability_factory.execution.validate_candidate", validate)
    report = Workflow(settings).run(RunRequest(description="运行取消后仍保存终止证据", provider="mock", max_candidates=1), cancel=cancellation)
    assert report["status"] == "cancelled"
    assert report["candidates"][0]["attempts"][0]["resources"]["worker_pid"] == 12345
    assert report["candidates"][0]["code_path"]


def test_nonrepairable_reviewer_keeps_failed_experience(settings, monkeypatch):
    original = MockProvider.generate

    def generate(self, role, system, payload, **kwargs):
        value = original(self, role, system, payload, **kwargs)
        if role == "reviewer":
            value["repairable"] = False
        return value

    monkeypatch.setattr(MockProvider, "generate", generate)
    report = Workflow(settings).run(RunRequest(description="保留无法修复的失败经验", provider="mock", max_candidates=1, inject_failure=True))
    assert report["status"] == "failed"
    assert report["knowledge_writeback"]["experiences"][0]["validated"] is False


def test_report_write_failure_cannot_leave_terminal_success(settings, monkeypatch):
    monkeypatch.setattr("capability_factory.execution.validate_candidate", lambda *args, **kwargs: {"status": "passed", "metrics": {"average_precision": 0.5}})

    def fail_report(*args, **kwargs):
        raise OSError("fixture disk failure")

    monkeypatch.setattr("capability_factory.workflow.write_report", fail_report)
    report = Workflow(settings).run(RunRequest(description="报告输出失败应明确标记失败", provider="mock", max_candidates=1))
    assert report["status"] == "failed"
    assert "Finalization" in report["failure_reason"]
    assert KnowledgeStore(settings.db_path).get_run(report["run_id"])["status"] == "failed"


def test_curator_failure_does_not_leave_passed_status(settings, monkeypatch):
    original = MockProvider.generate

    def generate(self, role, system, payload, **kwargs):
        if role == "curator":
            raise ProviderError("fixture upstream failure")
        return original(self, role, system, payload, **kwargs)

    monkeypatch.setattr(MockProvider, "generate", generate)
    monkeypatch.setattr("capability_factory.execution.validate_candidate", lambda *args, **kwargs: {"status": "passed", "metrics": {"average_precision": 0.5}})
    report = Workflow(settings).run(RunRequest(description="总结服务失败不能标记完整闭环成功", provider="mock", max_candidates=1))
    assert report["status"] == "failed"
    assert report["candidates"][0]["status"] == "passed"
