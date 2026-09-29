"""Documented CLI commands share the same services as the HTTP interface."""

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Annotated

import httpx
import typer

from capability_factory import prompts
from capability_factory.contracts import RunRequest
from capability_factory.inference import local_profile_metadata
from capability_factory.knowledge import KnowledgeStore
from capability_factory.providers import HTTPProvider, ProviderError
from capability_factory.reporting import write_report
from capability_factory.settings import load_settings
from capability_factory.workflow import Workflow, now, write_json

app = typer.Typer(help="AlgoForge: verifiable algorithm generation, evidence and bounded repair", no_args_is_help=True,
                  pretty_exceptions_show_locals=False)


def output(value):
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2, default=str))


@app.command()
def init(provider: Annotated[str, typer.Option(help="mock seeds only; deepseek or local_http performs real extraction")] = "mock"):
    """Initialize knowledge and optionally extract capabilities with the selected provider."""
    settings = load_settings()
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    if provider not in {"mock", "deepseek", "local_http"}:
        raise typer.BadParameter("provider must be mock, deepseek or local_http")
    remote = HTTPProvider(settings, mode=provider) if provider in {"deepseek", "local_http"} else None
    extraction = {}

    def extractor(sources):
        approved_keys = {"bank-duration", "project-bank-policy", "project-sms-split", "sklearn-pipeline",
                         "sklearn-columns", "sklearn-onehot", "sklearn-logistic", "sklearn-tfidf",
                         "sklearn-complementnb", "sklearn-ap"}
        selected = [{key: item.get(key) for key in ["source_id", "source_key", "uri", "revision", "locator", "content"]}
                    for item in sources if item.get("source_key") in approved_keys]
        result = remote.generate("extractor", prompts.EXTRACTOR, {"sources": selected}, max_tokens=4096)
        extraction.update({"mode": "real", "model": remote.model, "sources": selected, "result": result, "usage": remote.usage.as_dict()})
        return result

    try:
        summary = store.ingest_sources(settings.root, extractor=extractor if remote else None)
        summary["mode"] = "real_extraction" if remote and remote.usage.records else "manual_seed_ingestion"
        if remote:
            summary["usage"] = remote.usage.as_dict()
            destination = settings.root / "artifacts" / "ingestion" / f"{provider}_extraction.json"
            write_json(destination, {"created_at": now(), "summary": summary, **extraction})
            summary["extraction_artifact"] = str(destination)
        output({key: value for key, value in summary.items() if key not in {"sources", "source_manifest", "cards", "capabilities"}})
        if remote and (not remote.usage.records or not summary.get("llm_extracted_cards")):
            typer.echo("Real extraction did not yield validated source-grounded cards; inspect saved issues.", err=True)
            raise typer.Exit(1)
    except ProviderError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None


@app.command()
def run(
    description: Annotated[str, typer.Option(help="Natural-language algorithm request")],
    dataset: Annotated[str, typer.Option()] = "bank",
    provider: Annotated[str, typer.Option()] = "deepseek",
    max_candidates: Annotated[int, typer.Option()] = 2,
    max_repairs: Annotated[int, typer.Option()] = 2,
    search: Annotated[str, typer.Option()] = "compare",
    use_graph: Annotated[bool, typer.Option("--use-graph/--no-use-graph")] = True,
    use_retrieval: Annotated[bool, typer.Option("--use-retrieval/--no-use-retrieval")] = True,
    orchestration: Annotated[str, typer.Option()] = "multi_role",
    inject_failure: Annotated[bool, typer.Option()] = False,
    max_seconds: Annotated[int, typer.Option()] = 900,
):
    """Run the complete workflow and persist every candidate and verification result."""
    request = RunRequest(description=description, dataset_id=dataset, provider=provider, max_candidates=max_candidates,
                         max_repairs=max_repairs, search=search, use_graph=use_graph,
                         use_retrieval=use_retrieval, orchestration=orchestration,
                         inject_failure=inject_failure, max_seconds=max_seconds)
    report = Workflow(load_settings()).run(request)
    output({"run_id": report["run_id"], "status": report["status"], "mode": report["mode"],
            "model": report["model"], "selected_candidate_id": report["selected_candidate_id"],
            "candidates": [{"id": item["candidate_id"], "status": item["status"], "metrics": item["metrics"], "repairs": len(item["repairs"])} for item in report["candidates"]],
            "usage": {key: value for key, value in report["usage"].items() if key != "records"},
            "failure_reason": report.get("failure_reason"), "report_paths": report["report_paths"]})
    if report["status"] != "passed":
        raise typer.Exit(1)


@app.command()
def serve(host: Annotated[str, typer.Option()] = "127.0.0.1", port: Annotated[int, typer.Option()] = 8000):
    """Start the local FastAPI service and generated OpenAPI documentation."""
    import uvicorn

    from capability_factory.api import create_app

    uvicorn.run(create_app(), host=host, port=port)


@app.command()
def doctor(check_api: Annotated[bool, typer.Option()] = False):
    """Show prerequisites without exposing credentials; optional authenticated model discovery."""
    settings = load_settings()
    result = {"root": str(settings.root), "python": sys.version.split()[0], "model": settings.model,
              "credential_configured": bool(settings.api_key.get_secret_value()),
              "executor": "constrained_ast_subprocess", "arbitrary_python_execution": False,
              "docker_available": bool(shutil.which("docker")), "local_model_deployed": False,
              "local_provider": local_profile_metadata(settings),
              "datasets": {name: (settings.root / "data/raw" / name).is_file() for name in ["bank-additional-full.csv", "SMSSpamCollection"]}}
    if check_api:
        # Provider construction validates the destination before any credential is sent.
        HTTPProvider(settings)
        try:
            response = httpx.get(settings.base_url.rstrip("/") + "/models", headers={"Authorization": "Bearer " + settings.api_key.get_secret_value()}, timeout=20, follow_redirects=False, trust_env=False)
            if response.status_code == 200:
                result["models"] = [{"id": item["id"], "name": item.get("name")} for item in response.json()["data"]]
                result["api_status"] = "authenticated"
            else:
                result["api_status"] = f"HTTP {response.status_code}"
        except (httpx.TransportError, ValueError, KeyError):
            result["api_status"] = "connection_or_response_error"
    output(result)


@app.command("export-graph")
def export_graph(output_path: Annotated[Path, typer.Option("--output")] = Path("artifacts/graph.json")):
    """Export current graph as portable JSON with source and validation relationships."""
    settings = load_settings()
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    graph = store.graph()
    write_json(output_path, graph)
    output({"path": str(output_path), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])})


@app.command()
def report(run_id: str, format: Annotated[str, typer.Option()] = "html", output_path: Annotated[Path | None, typer.Option("--output")] = None):
    """Regenerate a JSON, HTML or Markdown report from persisted verification facts."""
    if format not in {"json", "html", "markdown"}:
        raise typer.BadParameter("format must be json, html or markdown")
    settings = load_settings()
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    value = store.get_run(run_id)
    if value is None:
        raise typer.BadParameter("Unknown run_id")
    paths = write_report(value, settings.runs_dir / run_id)
    source = Path(paths[format])
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output_path)
        source = output_path
    output({"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})


if __name__ == "__main__":
    app()
