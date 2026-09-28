"""Local API with bounded job concurrency and controlled artifact access."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from capability_factory.contracts import RunRequest
from capability_factory.knowledge import KnowledgeStore
from capability_factory.reporting import render_html
from capability_factory.settings import Settings, load_settings
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


def create_app(settings: Settings | None = None):
    settings = settings or load_settings()
    manager = RunManager(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        manager.close()

    app = FastAPI(title="AlgoForge 算法能力工厂", version="0.1.0", lifespan=lifespan)
    app.state.manager = manager

    def report_for(run_id):
        if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
            raise HTTPException(404, "Unknown run")
        report = manager.store.get_run(run_id)
        if report is None:
            raise HTTPException(404, "Unknown run")
        return report

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": "deepseek", "model": settings.model,
                "credential_configured": bool(settings.api_key.get_secret_value()),
                "sandbox": "constrained_ast_subprocess", "os_sandbox": False,
                "local_model_deployed": False, "max_parallel_runs": 2}

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

    @app.get("/runs/{run_id}/report")
    def report_json(run_id: str):
        return report_for(run_id)

    @app.get("/runs/{run_id}/report.html", response_class=HTMLResponse)
    def report_html(run_id: str):
        return render_html(report_for(run_id))

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

    @app.get("/graph")
    def graph():
        return manager.store.graph()

    return app
