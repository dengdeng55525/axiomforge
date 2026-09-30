"""LangChain role chains and a typed, read-only capability retrieval tool.

The workflow owns scheduling, budgets and repairs. Each role invocation composes
provider execution, local audit persistence and Pydantic parsing in a Runnable
sequence. Tracing stays local so payloads and credentials never enter LangSmith.
"""

from collections.abc import Callable
from importlib.metadata import version
from typing import Any, Literal

from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.tools import StructuredTool
from langsmith.run_helpers import tracing_context
from pydantic import BaseModel, ConfigDict, Field

from capability_factory.knowledge import KnowledgeStore


def runtime_metadata() -> dict[str, Any]:
    """Describe the execution framework without exposing provider configuration."""
    return {
        "framework": "langchain-core",
        "version": version("langchain-core"),
        "role_chain": ["invoke_provider", "persist_response", "validate_contract"],
        "retrieval_tool": "search_capabilities",
        "external_tracing": False,
    }


def invoke_role(
    provider: Any,
    role: str,
    system: str,
    payload: dict[str, Any],
    schema: type[BaseModel],
    max_tokens: int,
    checkpoint: Callable[[], None],
    on_response: Callable[[dict[str, Any]], None],
) -> BaseModel:
    """Execute one schema-checked role call; propagate errors to bounded repair."""
    def invoke(inputs: dict[str, Any]) -> dict[str, Any]:
        checkpoint()
        return provider.generate(role, system, inputs, max_tokens=max_tokens)

    def persist(data: dict[str, Any]) -> dict[str, Any]:
        on_response(data)
        checkpoint()
        return data

    chain = RunnableSequence(
        RunnableLambda(invoke, name="invoke_provider"),
        RunnableLambda(persist, name="persist_response"),
        RunnableLambda(schema.model_validate, name="validate_contract"),
        name=f"algoforge_{role}",
    )
    with tracing_context(enabled=False):
        return chain.invoke(payload, config={"tags": ["algoforge", role], "callbacks": []})


class CapabilitySearchInput(BaseModel):
    """Bounded retrieval arguments; storage access stays inside the service."""
    model_config = ConfigDict(extra="forbid", strict=True)

    query: str = Field(min_length=1, max_length=8000)
    task_type: Literal["tabular_binary_classification", "text_binary_classification"]
    limit: int = Field(default=6, ge=1, le=6)
    use_graph: bool = True


def capability_search_tool(
    store: KnowledgeStore, checkpoint: Callable[[], None],
) -> StructuredTool:
    """Expose task-filtered evidence retrieval without model-authored SQL or I/O."""
    def search(query: str, task_type: str, limit: int = 6, use_graph: bool = True):
        checkpoint()
        evidence = store.search(query, task_type, limit=limit, use_graph=use_graph)
        checkpoint()
        return evidence

    return StructuredTool.from_function(
        func=search,
        name="search_capabilities",
        description=("Retrieve versioned algorithm capability cards for the selected task, "
                     "including source citations, constraints and graph evidence paths."),
        args_schema=CapabilitySearchInput,
    )


def retrieve_capabilities(
    store: KnowledgeStore, checkpoint: Callable[[], None], **arguments: Any,
) -> list[dict[str, Any]]:
    """Invoke the actual LangChain tool while keeping all tracing local."""
    with tracing_context(enabled=False):
        return capability_search_tool(store, checkpoint).invoke(arguments, config={"callbacks": []})
