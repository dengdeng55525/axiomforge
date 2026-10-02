"""Serve the compiled workbench and a fixed same-origin UI gateway.

The gateway forwards only known API routes. It does not read credentials, own a
run manager, or execute generated code.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles


def mount_workbench(app: FastAPI, root: Path) -> None:
    distribution = root / "web" / "dist"

    @app.get("/", include_in_schema=False)
    def workbench_entry():
        return RedirectResponse("/app/")

    if (distribution / "index.html").is_file():
        app.mount("/app", StaticFiles(directory=distribution, html=True), name="workbench")
    else:
        @app.get("/app/", include_in_schema=False)
        def missing_workbench():
            return JSONResponse(
                {"detail": "Frontend is not built. Run scripts/build_web.sh then restart the service."},
                status_code=503,
            )


def create_ui_app(backend_url: str | None = None, root: Path | None = None) -> FastAPI:
    endpoint = (backend_url or os.environ.get("ALGOFORGE_API_URL", "http://127.0.0.1:8000")).rstrip("/")
    parsed = urlsplit(endpoint)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("ALGOFORGE_API_URL must be an HTTP(S) backend URL without credentials or query")
    project = root or Path(os.environ.get("ALGOFORGE_ROOT", Path(__file__).resolve().parents[2]))

    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(timeout=30, trust_env=False, follow_redirects=False) as client:
            app.state.backend_client = client
            yield

    app = FastAPI(title="AxiomForge · 知衡 Web Workbench", lifespan=lifespan, docs_url=None, redoc_url=None)
    mount_workbench(app, project)

    @app.api_route("/{path:path}", methods=["GET", "POST"], include_in_schema=False)
    async def proxy(path: str, request: Request):
        root_name = path.split("/")[0]
        if root_name not in {"health", "system", "harness", "runs", "graph", "capabilities", "config", "inference", "datasets"}:
            raise HTTPException(404, "Unknown API route")
        if ".." in path.split("/") or "\\" in path:
            raise HTTPException(400, "Invalid API path")
        if request.method == "POST" and root_name != "runs":
            raise HTTPException(405, "Unsupported write route")
        if request.method == "POST" and not (path == "runs" or (path.startswith("runs/") and path.endswith("/cancel"))):
            raise HTTPException(405, "Unsupported write route")
        body = await request.body()
        if len(body) > 65536:
            raise HTTPException(413, "Request exceeds the workbench input limit")
        target = endpoint + "/" + path
        if request.url.query:
            target += "?" + request.url.query
        try:
            result = await app.state.backend_client.request(
                request.method, target, content=body,
                headers={"content-type": request.headers.get("content-type", "application/json")},
            )
        except httpx.RequestError:
            raise HTTPException(502, "API 服务未连接，请先运行 scripts/start_api.sh。") from None
        return Response(
            content=result.content, status_code=result.status_code,
            headers={"content-type": result.headers.get("content-type", "application/json"), "cache-control": "no-store"},
        )

    return app
