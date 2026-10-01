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
from capability_factory.harness import evaluate_run, evaluate_suite, load_cases
from capability_factory.inference import local_profile_metadata
from capability_factory.knowledge import KnowledgeStore
from capability_factory.providers import HTTPProvider, OpenAIResponsesProvider, ProviderError
from capability_factory.reporting import write_report
from capability_factory.settings import load_settings
from capability_factory.workflow import Workflow, now, write_json

app = typer.Typer(help="AlgoForge: verifiable algorithm generation, evidence and bounded repair", no_args_is_help=True,
                  pretty_exceptions_show_locals=False)
harness_app = typer.Typer(help="Offline trace-based Agent evaluation harness", no_args_is_help=True,
                          pretty_exceptions_show_locals=False)
app.add_typer(harness_app, name="harness")


def output(value):
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2, default=str))


@app.command()
def init(provider: Annotated[str, typer.Option(help="mock seeds only; deepseek, openai or local_http performs real extraction")] = "mock"):
    """Initialize knowledge and optionally extract capabilities with the selected provider."""
    settings = load_settings()
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    if provider not in {"mock", "deepseek", "openai", "local_http"}:
        raise typer.BadParameter("provider must be mock, deepseek, openai or local_http")
    try:
        remote = (OpenAIResponsesProvider(settings) if provider == "openai" else
                  HTTPProvider(settings, mode=provider) if provider in {"deepseek", "local_http"} else None)
    except ProviderError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None
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
def doctor(
    check_api: Annotated[bool, typer.Option()] = False,
    provider: Annotated[str, typer.Option(help="deepseek or openai model discovery")] = "deepseek",
):
    """Show prerequisites without exposing credentials; optional authenticated model discovery."""
    settings = load_settings()
    if provider not in {"deepseek", "openai"}:
        raise typer.BadParameter("doctor --provider accepts deepseek or openai")
    def public_text(value):
        text = str(value)
        for credential in (settings.api_key, settings.openai_api_key, settings.local_api_key, settings.openai_proxy_url):
            secret = credential.get_secret_value()
            if secret:
                text = text.replace(secret, "[REDACTED]")
        return text[:512]

    selected_model = public_text(settings.openai_model if provider == "openai" else settings.model)
    selected_key = settings.openai_api_key if provider == "openai" else settings.api_key
    result = {"root": str(settings.root), "python": sys.version.split()[0], "model": selected_model,
              "provider": provider,
              "credential_configured": bool(selected_key.get_secret_value()),
              "executor": "constrained_ast_subprocess", "arbitrary_python_execution": False,
              "docker_available": bool(shutil.which("docker")), "local_model_deployed": False,
              "local_provider": local_profile_metadata(settings),
              "datasets": {name: (settings.root / "data/raw" / name).is_file() for name in ["bank-additional-full.csv", "SMSSpamCollection"]}}
    if check_api and provider == "openai":
        try:
            from openai import APIError, DefaultHttpxClient, OpenAI

            profile = OpenAIResponsesProvider(settings).metadata()
            transport = {"trust_env": False, "follow_redirects": False}
            if settings.openai_proxy_url.get_secret_value():
                transport["proxy"] = settings.openai_proxy_url.get_secret_value()
            with OpenAI(api_key=selected_key.get_secret_value(), base_url=profile["base_url"],
                        max_retries=0, timeout=20,
                        http_client=DefaultHttpxClient(**transport)) as client:
                result["models"] = [{"id": public_text(item.id)} for item in client.models.list().data]
            result["api_status"] = "authenticated"
            result["deployment"] = profile["deployment"]
        except (APIError, ProviderError, ValueError, KeyError, AttributeError):
            result["api_status"] = "connection_or_response_error"
    elif check_api:
        # Provider construction validates the destination before any credential is sent.
        HTTPProvider(settings)
        try:
            response = httpx.get(settings.base_url.rstrip("/") + "/models", headers={"Authorization": "Bearer " + settings.api_key.get_secret_value()}, timeout=20, follow_redirects=False, trust_env=False)
            if response.status_code == 200:
                result["models"] = [{"id": public_text(item["id"]), "name": public_text(item["name"]) if item.get("name") else None} for item in response.json()["data"]]
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


@app.command("ingest-repo")
def ingest_repo(
    repository: Path,
    paths: Annotated[list[str], typer.Option("--path", help="Repeat for each committed Python file")],
    repository_url: Annotated[str, typer.Option(help="Credential-free HTTPS source repository URL")],
    license_id: Annotated[str, typer.Option("--license")],
    task_types: Annotated[list[str], typer.Option("--task-type")],
    revision: Annotated[str, typer.Option()] = "HEAD",
    output_path: Annotated[Path, typer.Option("--output")] = Path("artifacts/ingestion/repository.json"),
):
    """Extract committed source through AST and version its source-grounded capability cards."""
    from capability_factory.repository import extract_repository

    try:
        manifest = extract_repository(repository, paths, repository_url=repository_url,
                                      license_id=license_id, task_types=task_types, revision=revision)
        summary = KnowledgeStore(load_settings().db_path).ingest_repository(manifest)
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from None
    write_json(output_path, manifest)
    output({**summary, "manifest": str(output_path), "source_executed": False})


@app.command("export-openapi")
def export_openapi(output_path: Annotated[Path, typer.Option("--output")] = Path("artifacts/openapi.json")):
    """Generate the live API contract offline without loading credentials or modifying live data."""
    from tempfile import TemporaryDirectory

    from capability_factory.api import create_app
    from capability_factory.settings import Settings

    with TemporaryDirectory(prefix="algoforge-openapi-") as temporary:
        application = create_app(Settings(root=Path(temporary)))
        try:
            schema = application.openapi()
        finally:
            application.state.manager.close()
            application.state.manager.store.close()
    write_json(output_path, schema)
    output({"path": str(output_path), "openapi": schema["openapi"], "paths": len(schema["paths"])})


@app.command("analyze-run")
def analyze_run(
    run_id: str,
    output_path: Annotated[Path | None, typer.Option("--output")] = None,
):
    """Compare observed AP, training time and memory with a within-run Pareto frontier."""
    from capability_factory.optimization import analyze_resources

    store = KnowledgeStore(load_settings().db_path)
    store.initialize()
    saved = store.get_run(run_id)
    if saved is None:
        raise typer.BadParameter("Unknown run ID")
    analysis = analyze_resources(saved)
    if output_path is not None:
        write_json(output_path, analysis)
    output(analysis)


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


@harness_app.command("cases")
def harness_cases(
    cases_path: Annotated[Path | None, typer.Option("--cases", help="Versioned harness case JSON")] = None,
):
    """List deterministic evaluation rubrics without loading a model or running a job."""
    settings = load_settings()
    path = cases_path or settings.root / "configs" / "agent_harness_cases.json"
    try:
        cases = load_cases(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error)) from None
    output({"schema_version": "agent-harness.v1", "path": str(path),
            "cases": [item.model_dump() for item in cases]})


@harness_app.command("evaluate")
def harness_evaluate(
    run_id: Annotated[str, typer.Argument(help="Persisted 32-character run identifier")],
    case_id: Annotated[str, typer.Option("--case", help="Harness rubric ID")] = "bank_e2e",
    cases_path: Annotated[Path | None, typer.Option("--cases", help="Versioned harness case JSON")] = None,
    output_path: Annotated[Path | None, typer.Option("--output", help="Optional JSON result path")] = None,
):
    """Evaluate a saved run using the local harness; this command is read-only."""
    settings = load_settings()
    path = cases_path or settings.root / "configs" / "agent_harness_cases.json"
    try:
        cases = load_cases(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error)) from None
    case = next((item for item in cases if item.id == case_id), None)
    if case is None:
        raise typer.BadParameter(f"Unknown harness case: {case_id}")
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    try:
        try:
            result = evaluate_run(store, run_id, case)
        except KeyError:
            raise typer.BadParameter(f"Unknown run ID: {run_id}") from None
    finally:
        store.close()
    payload = result.model_dump(mode="json")
    if output_path is not None:
        write_json(output_path, payload)
        payload["output_path"] = str(output_path)
    output(payload)
    if not result.passed:
        raise typer.Exit(1)


@harness_app.command("replay")
def harness_replay(
    run_id: Annotated[str, typer.Argument(help="Persisted 32-character run identifier")],
    through_sequence: Annotated[int | None, typer.Option("--through", min=0, help="Replay cursor sequence")] = None,
):
    """Print a cursor-bounded, redacted Agent trace for local debugging."""
    settings = load_settings()
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    try:
        report = store.get_run(run_id)
        if report is None:
            raise typer.BadParameter(f"Unknown run ID: {run_id}")
        from capability_factory.observability import build_agent_trace

        try:
            trace = build_agent_trace(report, through_sequence=through_sequence)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from None
    finally:
        store.close()
    output(trace)


@harness_app.command("suite")
def harness_suite(
    run_id: Annotated[str, typer.Argument(help="Persisted 32-character run identifier")],
    cases_path: Annotated[Path | None, typer.Option("--cases", help="Versioned harness case JSON")] = None,
    output_path: Annotated[Path | None, typer.Option("--output", help="Optional JSON result path")] = None,
):
    """Run every registered rubric and produce one aggregate regression artifact."""
    settings = load_settings()
    path = cases_path or settings.root / "configs" / "agent_harness_cases.json"
    try:
        cases = load_cases(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error)) from None
    store = KnowledgeStore(settings.db_path)
    store.initialize()
    try:
        report = store.get_run(run_id)
        if report is None:
            raise typer.BadParameter(f"Unknown run ID: {run_id}")
        payload = evaluate_suite(report, cases)
    finally:
        store.close()
    if output_path is not None:
        write_json(output_path, payload)
        payload["output_path"] = str(output_path)
    output(payload)
    if not payload["passed"]:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
