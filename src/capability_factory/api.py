"""Local API with bounded job concurrency and controlled artifact access."""

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from capability_factory import __version__
from capability_factory.agent_runtime import runtime_metadata
from capability_factory.contracts import RunRequest
from capability_factory.gpu_status import probe_gpus
from capability_factory.graph_presentation import (
    capability_detail,
    explore_graph,
    quality_label,
    summarize_checks,
)
from capability_factory.harness import evaluate_report, evaluate_suite, load_cases
from capability_factory.inference import load_inference_profiles, local_profile_metadata
from capability_factory.knowledge import KnowledgeStore
from capability_factory.knowledge_governance import validate_store
from capability_factory.observability import build_agent_trace
from capability_factory.optimization import analyze_resources
from capability_factory.providers import OpenAIResponsesProvider, ProviderError
from capability_factory.reporting import render_html, render_markdown
from capability_factory.reproducibility import build_reproducibility
from capability_factory.settings import Settings, load_settings
from capability_factory.webui import mount_workbench
from capability_factory.workflow import Workflow, now


class RunManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = KnowledgeStore(settings.db_path)
        self.store.initialize()
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="algoforge")
        self.lock = threading.Lock()
        self.jobs = {}

    def launch(self, request: RunRequest):
        with self.lock:
            active = sum(not entry["future"].done() for entry in self.jobs.values())
            if active >= 8:
                raise HTTPException(status_code=429, detail="Run queue is full; wait for active work")
            run_id = uuid.uuid4().hex
            cancel = threading.Event()
            self.store.save_run({"run_id": run_id, "status": "queued", "mode": "mock" if request.provider == "mock" else "real",
                                 "description": request.description, "dataset_id": request.dataset_id, "created_at": now(),
                                 "request": request.model_dump(), "candidates": [], "events": []})
            future = self.pool.submit(Workflow(self.settings, self.store).run, request, run_id, cancel)
            self.jobs[run_id] = {"future": future, "cancel": cancel}
            future.add_done_callback(lambda completed, task_id=run_id: self.reconcile(task_id, completed))
        return {"run_id": run_id, "status": "queued"}

    def reconcile(self, run_id, future):
        """Persist a terminal state even when setup or report finalization raises."""
        failed = future.cancelled()
        error = None if failed else future.exception()
        if not failed and error is None:
            return
        report = self.store.get_run(run_id) or {"run_id": run_id}
        report["status"] = "cancelled" if failed else "failed"
        message = "Cancelled before execution" if failed else f"Unhandled {type(error).__name__} in run service"
        report["failure_reason"] = message
        report["finished_at"] = now()
        self.store.save_run(report)

    def close(self):
        for entry in self.jobs.values():
            entry["cancel"].set()
        self.pool.shutdown(wait=False, cancel_futures=True)


def _safe_endpoint(value: str) -> str | None:
    """Return a display-only URL with credentials and query state removed.

    Provider configuration is shown in the visual client, so this helper must not
    echo an accidental ``user:password@host`` or signed query URL from a deployer's
    environment.  It deliberately does not perform a network request.
    """
    try:
        parsed = urlsplit(str(value))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return None
        hostname = parsed.hostname
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = hostname
        if parsed.port:
            netloc += f":{parsed.port}"
        path = parsed.path.rstrip("/")
        return urlunsplit((parsed.scheme, netloc, path, "", ""))
    except (TypeError, ValueError):
        return None


def _provider_catalog(settings: Settings) -> dict:
    """Safe provider profiles consumed by the visual workflow client.

    ``local_http`` is intentionally advertised as a planned OpenAI-compatible
    endpoint.  AxiomForge does not start it, download weights, or probe arbitrary
    URLs; the deployment status remains explicit until an operator runs the local
    serving stack.
    """
    key_configured = bool(settings.api_key.get_secret_value())
    remote_endpoint = _safe_endpoint(settings.base_url)
    local_endpoints = [_safe_endpoint(value) for value in settings.local_endpoints]
    local_endpoints = [value for value in local_endpoints if value]
    local_endpoint = local_endpoints[0] if local_endpoints else None
    openai_configured = bool(settings.openai_api_key.get_secret_value())
    openai_endpoint = _safe_endpoint(settings.openai_base_url)
    parsed_openai = urlsplit(openai_endpoint or "")
    openai_deployment = ("official_api" if parsed_openai.hostname == "api.openai.com"
                         else "openai_compatible_api")
    openai_available = False
    openai_status = "missing_credentials"
    if openai_configured:
        try:
            metadata = OpenAIResponsesProvider(settings).metadata()
            openai_endpoint = metadata["base_url"]
            openai_deployment = metadata["deployment"]
            openai_available = True
            openai_status = "configured"
        except ProviderError:
            openai_endpoint = None
            openai_status = "invalid_configuration"
    openai_model = settings.openai_model
    for credential in (settings.api_key, settings.openai_api_key, settings.local_api_key, settings.openai_proxy_url):
        secret = credential.get_secret_value()
        if secret:
            openai_model = openai_model.replace(secret, "[REDACTED]")
    return {
        "schema_version": "1.0",
        "default_provider": "deepseek",
        "agent_runtime": runtime_metadata(),
        "providers": [
            {
                "id": "deepseek",
                "label": "DeepSeek API",
                "kind": "remote_api",
                "model": settings.model,
                "endpoint": remote_endpoint,
                "configured": key_configured,
                "available": key_configured and remote_endpoint is not None,
                "status": "configured" if key_configured else "missing_credentials",
                "requires_api_key": True,
                "local_model_deployed": False,
                "capabilities": ["structured_json", "multi_role", "beam_search"],
            },
            {
                "id": "openai",
                "label": "OpenAI / Responses API",
                "kind": "remote_api",
                "deployment": openai_deployment,
                "api": "responses",
                "sdk": "openai",
                "model": openai_model,
                "endpoint": openai_endpoint,
                "configured": openai_configured,
                "available": openai_available,
                "status": openai_status,
                "requires_api_key": True,
                "local_model_deployed": False,
                "capabilities": ["structured_json", "multi_role", "beam_search", "responses"],
            },
            {
                "id": "local_http",
                "label": "本地大模型（OpenAI 兼容）",
                "kind": "local_openai_compatible",
                "model": settings.local_model,
                "endpoint": local_endpoint,
                "configured": bool(local_endpoints),
                "available": False,
                "status": "operator_managed",
                "requires_api_key": False,
                "local_model_deployed": False,
                "model_plan": {
                    "model_family": "Qwen2.5-Coder-14B-Instruct-AWQ",
                    "profile": "four_gpu_14b",
                    "gpu_count": 4,
                    "tensor_parallel_size": 1,
                    "serving_stack": "vllm_openai_compatible",
                    "ports": [8100, 8101, 8102, 8103],
                    "weights_managed_by_algoforge": False,
                },
                "endpoints": local_endpoints,
                "endpoint_count": len(local_endpoints),
                "capabilities": ["structured_json", "multi_role", "beam_search"],
            },
            {
                "id": "mock",
                "label": "Mock（工程流程验证）",
                "kind": "deterministic_mock",
                "model": "deterministic-mock-v1",
                "endpoint": None,
                "configured": True,
                "available": True,
                "status": "ready",
                "requires_api_key": False,
                "local_model_deployed": False,
                "capabilities": ["structured_json", "multi_role", "beam_search"],
            },
        ],
    }


def _safe_local_profile(settings: Settings) -> dict:
    """Sanitize the static local profile before exposing it over HTTP."""
    profile = dict(local_profile_metadata(settings))
    safe_urls = [_safe_endpoint(value) for value in settings.local_endpoints]
    safe_urls = [value for value in safe_urls if value]
    profile["base_urls"] = safe_urls
    profile["base_url"] = safe_urls[0] if safe_urls else None
    profile["endpoint_count"] = len(safe_urls)
    profile["configured"] = bool(safe_urls)
    return profile


def _dataset_catalog(settings: Settings) -> list[dict]:
    """Public dataset contracts for the UI; never returns raw data or paths."""
    bank_raw = settings.root / "data" / "raw" / "bank-additional-full.csv"
    sms_raw = settings.root / "data" / "raw" / "SMSSpamCollection"
    return [
        {
            "id": "bank",
            "canonical_id": "uci-bank-additional-full",
            "label": "UCI Bank Marketing",
            "task_type": "tabular_binary_classification",
            "source_url": "https://archive.ics.uci.edu/dataset/222/bank+marketing",
            "license": "CC BY 4.0",
            "feature_policy": "precontact_conservative_v1",
            "feature_count": 10,
            "train_rows": 24712,
            "validation_rows": 8238,
            "sealed_test_rows": 8238,
            "sealed_test_scored": False,
            "available": bank_raw.is_file(),
            "positive_label": "yes",
            "primary_metric": "average_precision",
        },
        {
            "id": "sms",
            "canonical_id": "uci-sms-spam",
            "label": "UCI SMS Spam Collection",
            "task_type": "text_binary_classification",
            "source_url": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
            "license": "CC BY 4.0",
            "feature_policy": "text_only_group_dedup_v1",
            "feature_count": 1,
            "train_rows": 3095,
            "validation_rows": 1032,
            "sealed_test_rows": 1032,
            "sealed_test_scored": False,
            "available": sms_raw.is_file(),
            "positive_label": "spam",
            "primary_metric": "average_precision",
        },
    ]


def _finite(value):
    """Keep API aggregates JSON-safe without converting absent values to zero."""
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _metric_summary(report: dict) -> dict:
    candidates = [item for item in report.get("candidates", []) if isinstance(item, dict)]
    rows = []
    for candidate in candidates:
        plan = candidate.get("plan") if isinstance(candidate.get("plan"), dict) else {}
        metrics = candidate.get("metrics") if isinstance(candidate.get("metrics"), dict) else {}
        rows.append({
            "candidate_id": candidate.get("candidate_id"),
            "algorithm": plan.get("algorithm"),
            "variant": plan.get("variant"),
            "parent_id": candidate.get("parent_id") or plan.get("parent_id"),
            "status": candidate.get("status"),
            "quality_status": candidate.get("quality_status"),
            "quality_label": quality_label(candidate.get("quality_status")),
            "metrics": metrics,
            "checks": summarize_checks(candidate.get("checks"))["items"],
            "checks_summary": summarize_checks(candidate.get("checks")),
        })
    scored = [(row["candidate_id"], row["metrics"].get("average_precision")) for row in rows
              if isinstance(row["metrics"].get("average_precision"), (int, float))]
    best_id, best_ap = max(scored, key=lambda pair: pair[1]) if scored else (None, None)
    statuses = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "run_id": report.get("run_id"),
        "status": report.get("status"),
        "dataset_id": report.get("dataset_id"),
        "primary_metric": (report.get("task_spec") or {}).get("primary_metric", "average_precision"),
        "selected_candidate_id": report.get("selected_candidate_id"),
        "quality_status": report.get("quality_status"),
        "candidate_count": len(rows),
        "candidate_status_counts": statuses,
        "best_observed_average_precision": best_ap,
        "best_observed_candidate_id": best_id,
        "candidates": rows,
    }


def _resource_summary(report: dict) -> dict:
    candidates = [item for item in report.get("candidates", []) if isinstance(item, dict)]
    rows = []
    for candidate in candidates:
        resources = candidate.get("resources") if isinstance(candidate.get("resources"), dict) else {}
        rows.append({
            "candidate_id": candidate.get("candidate_id"),
            "status": candidate.get("status"),
            "wall_seconds": _finite(resources.get("wall_seconds")),
            "total_seconds": _finite(resources.get("total_seconds")),
            "fit_seconds": _finite(resources.get("fit_seconds")),
            "predict_seconds": _finite(resources.get("predict_seconds")),
            "cpu_seconds": _finite(resources.get("cpu_seconds")),
            "peak_rss_mib": _finite(resources.get("peak_rss_mib")),
            "limits": resources.get("limits") if isinstance(resources.get("limits"), dict) else {},
        })
    observed_rss = [row["peak_rss_mib"] for row in rows if row["peak_rss_mib"] is not None]
    observed_wall = [row["wall_seconds"] for row in rows if row["wall_seconds"] is not None]
    usage = report.get("usage") if isinstance(report.get("usage"), dict) else {}
    timing = report.get("timing") if isinstance(report.get("timing"), dict) else {}
    return {
        "run_id": report.get("run_id"),
        "status": report.get("status"),
        "usage": {key: usage.get(key) for key in ("calls", "input_tokens", "output_tokens", "cached_input_tokens")
                  if usage.get(key) is not None},
        "timing": timing,
        "candidate_count": len(rows),
        "observed_candidate_resources": len(observed_wall),
        "peak_candidate_rss_mib": max(observed_rss) if observed_rss else None,
        "sum_candidate_wall_seconds": sum(observed_wall) if observed_wall else None,
        "candidates": rows,
    }


def create_app(settings: Settings | None = None):
    settings = settings or load_settings()
    manager = RunManager(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        manager.close()

    app = FastAPI(title="AxiomForge · 知衡", version=__version__, lifespan=lifespan)
    app.state.manager = manager

    def report_for(run_id):
        if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
            raise HTTPException(404, "Unknown run")
        report = manager.store.get_run(run_id)
        if report is None:
            raise HTTPException(404, "Unknown run")
        # Historical reports gain a versioned derived view without rewriting stored facts.
        if "optimization" not in report:
            report["optimization"] = analyze_resources(report)
        report["agent_trace"] = build_agent_trace(report)
        return report

    @app.get("/health")
    def health():
        local_provider = _safe_local_profile(settings)
        gpu_status = probe_gpus(local_provider.get("gpu_count") or 4)
        return {"status": "ok", "provider": "deepseek", "model": settings.model,
                "credential_configured": bool(settings.api_key.get_secret_value()),
                "sandbox": "constrained_ast_subprocess", "os_sandbox": False,
                "local_model_deployed": False, "local_provider": local_provider,
                "gpu_status": gpu_status,
                "max_parallel_runs": 2}

    @app.get("/system/gpus")
    def system_gpus():
        """Return a bounded read-only GPU snapshot for the visual console."""
        local_provider = _safe_local_profile(settings)
        return probe_gpus(local_provider.get("gpu_count") or 4)

    @app.get("/inference/profiles")
    def inference_profiles():
        """Expose static local deployment plans for the visual console.

        The response is configuration only.  This endpoint deliberately does
        not probe or launch a local model server.
        """

        config = load_inference_profiles(settings.root)
        return {
            "schema_version": config.get("schema_version"),
            "status": config.get("status"),
            "local_runtime": config.get("local_runtime", {}),
            "active_local": _safe_local_profile(settings),
            "models": config.get("models", {}),
            "profiles": config.get("profiles", {}),
        }

    @app.get("/config/providers")
    def provider_config():
        """Return provider choices without credentials or hidden settings."""
        return _provider_catalog(settings)

    @app.get("/config/datasets")
    def dataset_config():
        """Return the public data contracts used by the visual console."""
        return {"datasets": _dataset_catalog(settings)}

    @app.get("/datasets")
    def datasets():
        """Short alias for clients that only need the dataset catalog."""
        return {"datasets": _dataset_catalog(settings)}

    @app.get("/config")
    def public_config():
        """Return bounded, non-secret UI configuration in one request."""
        return {
            "schema_version": "1.0",
            "service": {"name": "AxiomForge · 知衡", "version": __version__},
            "providers": _provider_catalog(settings),
            "datasets": _dataset_catalog(settings),
            "limits": {
                "max_candidates": {"min": 1, "max": 6},
                "max_repairs": {"min": 0, "max": 2},
                "max_parallel_runs": 2,
                "run_queue_limit": 8,
            },
            "execution": {
                "validator": "constructor_only_ast",
                "sandbox": "constrained_ast_subprocess",
                "os_sandbox": False,
                "sealed_test_scored": False,
            },
        }

    @app.post("/runs", status_code=202)
    def submit(request: RunRequest):
        return manager.launch(request)

    @app.get("/runs")
    def runs():
        return {"runs": manager.store.list_runs(limit=50)}

    @app.get("/runs/{run_id}")
    def status(run_id: str):
        return report_for(run_id)

    @app.get("/runs/{run_id}/events")
    def events(run_id: str):
        return {"events": report_for(run_id).get("events", [])}

    @app.get("/runs/{run_id}/timeline")
    def timeline(run_id: str):
        """Compact event stream intended for a progress/timeline visualization."""
        report = report_for(run_id)
        all_events = report.get("events", [])
        compact = []
        for event in all_events if isinstance(all_events, list) else []:
            if not isinstance(event, dict):
                continue
            data = event.get("data") if isinstance(event.get("data"), dict) else {}
            compact.append({
                "sequence": event.get("sequence"),
                "event_type": event.get("event_type", event.get("type")),
                "created_at": event.get("created_at"),
                "role": data.get("role"),
                "candidate_id": data.get("candidate_id"),
                "attempt": data.get("attempt"),
                "status": data.get("status"),
                "message": data.get("message") or data.get("error"),
            })
        return {"run_id": run_id, "status": report.get("status"), "events": compact,
                "event_count": len(compact), "last_event": compact[-1] if compact else None}

    @app.get("/runs/{run_id}/agent-trace")
    def agent_trace(run_id: str, through_sequence: int | None = Query(default=None, ge=0)):
        """Return a safe Agent/tool trace or a cursor-bounded replay projection."""
        try:
            return build_agent_trace(report_for(run_id), through_sequence=through_sequence)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None

    @app.get("/runs/{run_id}/reproducibility")
    def reproducibility(run_id: str):
        """Return SHA-256 evidence for inputs, code, validation, and reports."""
        report = report_for(run_id)
        return build_reproducibility(report, settings.runs_dir / run_id)

    @app.get("/harness/cases")
    def harness_cases():
        """List local, versioned Agent evaluation rubrics."""
        path = settings.root / "configs" / "agent_harness_cases.json"
        try:
            cases = load_cases(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise HTTPException(status_code=500, detail=f"Invalid harness case catalog: {error}") from None
        return {"schema_version": "agent-harness.v1", "cases": [case.model_dump() for case in cases]}

    @app.get("/runs/{run_id}/harness")
    def harness_run(run_id: str, case_id: str = Query("bank_e2e", min_length=2, max_length=64)):
        """Evaluate a saved run with the local harness without mutating it."""
        path = settings.root / "configs" / "agent_harness_cases.json"
        try:
            cases = load_cases(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise HTTPException(status_code=500, detail=f"Invalid harness case catalog: {error}") from None
        case = next((item for item in cases if item.id == case_id), None)
        if case is None:
            raise HTTPException(status_code=404, detail="Unknown harness case")
        try:
            result = evaluate_report(report_for(run_id), case)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        return result.model_dump(mode="json")

    @app.get("/runs/{run_id}/harness-suite")
    def harness_suite(run_id: str):
        """Evaluate all registered local Agent rubrics as one regression suite."""
        path = settings.root / "configs" / "agent_harness_cases.json"
        try:
            cases = load_cases(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise HTTPException(status_code=500, detail=f"Invalid harness case catalog: {error}") from None
        return evaluate_suite(report_for(run_id), cases)

    @app.get("/runs/{run_id}/report")
    def report_json(run_id: str):
        return report_for(run_id)

    @app.get("/runs/{run_id}/metrics")
    def metrics(run_id: str):
        return _metric_summary(report_for(run_id))

    @app.get("/runs/{run_id}/resources")
    def resources(run_id: str):
        return _resource_summary(report_for(run_id))

    @app.get("/runs/{run_id}/summary")
    def summary(run_id: str):
        report = report_for(run_id)
        metric_report = _metric_summary(report)
        resource_report = _resource_summary(report)
        all_events = report.get("events") if isinstance(report.get("events"), list) else []
        selected = next((candidate for candidate in metric_report["candidates"]
                         if candidate["candidate_id"] == report.get("selected_candidate_id")), {})
        quality = report.get("quality_status") or selected.get("quality_status")
        return {
            "run_id": report.get("run_id"),
            "status": report.get("status"),
            "provider": report.get("provider"),
            "mode": report.get("mode"),
            "model": report.get("model"),
            "dataset_id": report.get("dataset_id"),
            "description": report.get("description"),
            "created_at": report.get("created_at"),
            "finished_at": report.get("finished_at"),
            "selected_candidate_id": report.get("selected_candidate_id"),
            "quality_status": quality,
            "quality_label": quality_label(quality),
            "candidate_count": metric_report["candidate_count"],
            "event_count": len(all_events),
            "metrics": metric_report,
            "resources": resource_report,
            "warnings": report.get("warnings", []),
            "validation": {
                "selected_candidate_id": report.get("selected_candidate_id"),
                "checks": selected.get("checks_summary", summarize_checks(None)),
                "quality_status": quality,
                "quality_label": quality_label(quality),
                "quality_gate_note": "AP 基线比较属于验证集建议性门槛；生产就绪与封存测试集成绩需要独立评估。",
            },
        }

    @app.get("/runs/{run_id}/report.html", response_class=HTMLResponse)
    def report_html(run_id: str):
        return render_html(report_for(run_id))

    @app.get("/runs/{run_id}/report.md", response_class=PlainTextResponse)
    def report_markdown(run_id: str):
        """Serve the readable Markdown report for review systems and notebooks."""
        return PlainTextResponse(render_markdown(report_for(run_id)), media_type="text/markdown")

    @app.get("/runs/{run_id}/artifacts")
    def artifacts(run_id: str):
        report = report_for(run_id)
        return {"artifacts": [{"artifact_id": item["artifact_id"], "candidate_id": item["candidate_id"],
                                "code_sha256": item.get("code_sha256"), "status": item["status"]}
                               for item in report.get("candidates", [])]}

    @app.get("/runs/{run_id}/artifacts/{artifact_id}")
    def artifact(run_id: str, artifact_id: str):
        report = report_for(run_id)
        candidate = next((item for item in report.get("candidates", []) if item.get("artifact_id") == artifact_id), None)
        if not candidate or not candidate.get("code_path"):
            raise HTTPException(404, "Unknown artifact")
        allowed = (settings.runs_dir / run_id).resolve()
        path = (allowed / candidate["code_path"]).resolve()
        if not path.is_relative_to(allowed) or path.suffix != ".py" or not path.is_file():
            raise HTTPException(404, "Unknown artifact")
        if path.stat().st_size > 60000:
            raise HTTPException(413, "Artifact exceeds size limit")
        return {"artifact_id": artifact_id, "code": path.read_text(), "code_sha256": candidate.get("code_sha256")}

    @app.post("/runs/{run_id}/cancel")
    def cancel(run_id: str):
        report = report_for(run_id)
        if report["status"] not in {"queued", "running"}:
            return {"run_id": run_id, "status": report["status"], "cancel_requested": False}
        with manager.lock:
            entry = manager.jobs.get(run_id)
            if entry is None:
                raise HTTPException(409, "Run is not controlled by this process; inspect previous service instance")
            entry["cancel"].set()
        return {"run_id": run_id, "status": report["status"], "cancel_requested": True}

    @app.get("/capabilities")
    def capabilities():
        return {"capabilities": manager.store.list_capabilities()}

    @app.get("/knowledge/quality")
    def knowledge_quality():
        """Return the read-only capability graph quality gate for the console."""
        return validate_store(manager.store)

    @app.get("/capabilities/{capability_id}")
    def capability(capability_id: str, version: int | None = Query(None, ge=1)):
        """Inspect the latest or a specific immutable capability version."""
        try:
            return capability_detail(manager.store, capability_id, version)
        except KeyError:
            raise HTTPException(404, "Unknown capability or version") from None

    @app.get("/graph/explore")
    def graph_explore(
        focus: str | None = Query(None, max_length=512),
        hops: int = Query(1, ge=1, le=2),
        kinds: str = Query("", max_length=512),
        relations: str = Query("", max_length=1024),
        q: str = Query("", max_length=200),
        limit: int = Query(120, ge=1, le=500),
        edge_limit: int = Query(300, ge=0, le=1500),
    ):
        """Bounded graph overview or neighborhood with auditable evidence.

        Kinds and relations accept comma-separated exact values. Relationships
        constrain traversal; kind/text filters constrain display, preserving an
        existing focus node. The legacy unfiltered /graph endpoint is unchanged.
        """
        try:
            return explore_graph(
                manager.store, focus=focus or None, hops=hops,
                kinds=[value.strip() for value in kinds.split(",") if value.strip()],
                relations=[value.strip() for value in relations.split(",") if value.strip()],
                query=q, limit=limit, edge_limit=edge_limit,
            )
        except KeyError:
            raise HTTPException(404, "Unknown graph focus node") from None

    @app.get("/graph")
    def graph():
        return manager.store.graph()

    mount_workbench(app, settings.root)
    return app
