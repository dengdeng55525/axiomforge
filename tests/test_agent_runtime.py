"""Actual LangChain composition, validation, cancellation and trace isolation."""

from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableSequence
from langchain_core.tools import StructuredTool
from langsmith.run_helpers import get_tracing_context
from pydantic import ValidationError

from capability_factory import agent_runtime
from capability_factory.contracts import TaskInterpretation


def test_role_chain_invokes_provider_then_persists_before_validation(monkeypatch):
    order = []
    metadata = []
    original = RunnableSequence.invoke

    def inspect(self, *args, **kwargs):
        metadata.append([step.name for step in self.steps])
        return original(self, *args, **kwargs)

    def generate(role, system, payload, max_tokens):
        assert (role, system, payload, max_tokens) == ("interpreter", "system", {"description": "hello"}, 300)
        order.append("provider")
        return {"objective": "hello"}

    monkeypatch.setattr(RunnableSequence, "invoke", inspect)
    result = agent_runtime.invoke_role(
        SimpleNamespace(generate=generate), "interpreter", "system", {"description": "hello"},
        TaskInterpretation, 300, lambda: order.append("checkpoint"),
        lambda data: order.append("persist"),
    )
    assert result.objective == "hello"
    assert order == ["checkpoint", "provider", "persist", "checkpoint"]
    assert metadata == [["invoke_provider", "persist_response", "validate_contract"]]


def test_invalid_schema_stays_auditable_and_propagates_to_workflow():
    audits = []
    with pytest.raises(ValidationError):
        agent_runtime.invoke_role(
            SimpleNamespace(generate=lambda *a, **k: {"unexpected": True}), "interpreter",
            "system", {}, TaskInterpretation, 300, lambda: None, audits.append,
        )
    assert audits == [{"unexpected": True}]


def test_checkpoint_prevents_provider_execution():
    calls = []

    def cancelled():
        raise RuntimeError("cancelled")

    with pytest.raises(RuntimeError, match="cancelled"):
        agent_runtime.invoke_role(
            SimpleNamespace(generate=lambda *a, **k: calls.append(True)), "interpreter",
            "system", {}, TaskInterpretation, 300, cancelled, lambda _: None,
        )
    assert calls == []


def test_provider_failure_propagates_without_hidden_framework_retry():
    calls = []

    def generate(*args, **kwargs):
        calls.append(True)
        raise RuntimeError("transport failed")

    with pytest.raises(RuntimeError, match="transport failed"):
        agent_runtime.invoke_role(
            SimpleNamespace(generate=generate), "interpreter", "system", {},
            TaskInterpretation, 300, lambda: None, lambda _: None,
        )
    assert len(calls) == 1


def test_retrieval_is_a_typed_tool_and_preserves_task_graph_filters():
    calls = []
    evidence = [{"capability_id": "cap-one", "evidence_path": []}]

    def search(*args, **kwargs):
        calls.append((args, kwargs))
        return evidence

    store = SimpleNamespace(search=search)
    tool = agent_runtime.capability_search_tool(store, lambda: None)
    assert isinstance(tool, StructuredTool)
    assert tool.name == "search_capabilities"
    result = agent_runtime.retrieve_capabilities(
        store, lambda: None, query="spam", task_type="text_binary_classification",
        limit=2, use_graph=False,
    )
    assert result == evidence
    assert calls == [(("spam", "text_binary_classification"), {"limit": 2, "use_graph": False})]


@pytest.mark.parametrize("overrides", [
    {"limit": 7}, {"limit": 0}, {"limit": True}, {"limit": "2"},
    {"query": ""}, {"query": "x" * 8001}, {"task_type": "arbitrary_sql"},
    {"use_graph": "true"}, {"sql": "DELETE FROM cf_runs"},
])
def test_tool_rejects_invalid_arguments_before_storage_access(overrides):
    calls = []
    store = SimpleNamespace(search=lambda *a, **k: calls.append(True))
    with pytest.raises(ValidationError):
        agent_runtime.retrieve_capabilities(
            store, lambda: None,
            **{"query": "bank", "task_type": "tabular_binary_classification", **overrides},
        )
    assert calls == []


def test_external_tracing_is_disabled_even_if_environment_enables_it(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    contexts = []

    def generate(*args, **kwargs):
        contexts.append(get_tracing_context()["enabled"])
        return {"objective": "offline"}

    def search(*args, **kwargs):
        contexts.append(get_tracing_context()["enabled"])
        return []

    agent_runtime.invoke_role(
        SimpleNamespace(generate=generate), "interpreter", "system", {},
        TaskInterpretation, 300, lambda: None, lambda _: None,
    )
    agent_runtime.retrieve_capabilities(
        SimpleNamespace(search=search), lambda: None,
        query="bank", task_type="tabular_binary_classification",
    )
    assert contexts == [False, False]
    assert agent_runtime.runtime_metadata()["external_tracing"] is False
