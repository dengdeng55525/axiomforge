"""Compiled UI routing and fixed-backend gateway contracts."""

import httpx
import pytest
from fastapi.testclient import TestClient

from capability_factory.api import create_app
from capability_factory.settings import Settings
from capability_factory.webui import create_ui_app


def test_workbench_mount_does_not_shadow_api_or_leak_repository(tmp_path):
    dist = tmp_path / "web" / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>AlgoForge app</html>")
    (dist / "assets" / "app.js").write_text("export const app = true")
    (tmp_path / ".env").write_text("DO_NOT_EXPOSE=fixture")
    with TestClient(create_app(Settings(root=tmp_path))) as client:
        assert client.get("/").text == "<html>AlgoForge app</html>"
        assert client.get("/app/assets/app.js").status_code == 200
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/app/.env").status_code == 404
        assert client.get("/runs").status_code == 200


def test_missing_build_is_actionable_and_does_not_break_api(tmp_path):
    with TestClient(create_app(Settings(root=tmp_path))) as client:
        assert client.get("/app/").status_code == 503
        assert "build_web.sh" in client.get("/app/").text
        assert client.get("/health").status_code == 200


def test_ui_gateway_uses_fixed_backend_and_preserves_reports(monkeypatch, tmp_path):
    seen = []

    async def request(self, method, url, **kwargs):
        seen.append((method, url, kwargs))
        return httpx.Response(200, json={"status": "passed"}, headers={"Content-Type": "application/json"})

    monkeypatch.setattr(httpx.AsyncClient, "request", request)
    with TestClient(create_ui_app("http://127.0.0.1:8000", tmp_path)) as client:
        result = client.get("/graph/explore?focus=capability:test:v1", headers={"Authorization": "secret-marker"})
        assert result.json() == {"status": "passed"}
        assert seen[0][1] == "http://127.0.0.1:8000/graph/explore?focus=capability:test:v1"
        assert "authorization" not in seen[0][2]["headers"]
        assert client.get("/system/gpus").status_code == 200
        assert seen[1][1] == "http://127.0.0.1:8000/system/gpus"
        assert client.get("/harness/cases").status_code == 200
        assert seen[2][1] == "http://127.0.0.1:8000/harness/cases"
        assert client.post("/runs", json={"description": "a new task"}).status_code == 200
        assert client.post("/runs/a/cancel").status_code == 200
        assert client.post("/config").status_code == 405
        assert client.get("/.env").status_code == 404
        assert client.post("/runs", content="a" * 65537).status_code == 413


def test_offline_api_has_visible_error(monkeypatch, tmp_path):
    async def request(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "request", request)
    with TestClient(create_ui_app(root=tmp_path)) as client:
        response = client.get("/health")
        assert response.status_code == 502
        assert "start_api.sh" in response.json()["detail"]


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://user:secret@localhost", "http://localhost?key=hidden"])
def test_ui_gateway_rejects_credential_or_non_http_urls(url, tmp_path):
    with pytest.raises(ValueError):
        create_ui_app(url, tmp_path)
