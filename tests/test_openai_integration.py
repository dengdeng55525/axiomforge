"""OpenAI wiring with offline LLM fixtures and real SMS algorithm validation.

No test sends a paid API request. The SMS test selects the actual Responses
provider and replaces only its generate method with labeled deterministic
responses; dataset preparation, compilation, evaluation and persistence run.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import openai
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from typer.testing import CliRunner

from capability_factory.api import create_app
from capability_factory.cli import app as cli_app
from capability_factory.contracts import RunRequest
from capability_factory.knowledge import KnowledgeStore
from capability_factory.providers import HTTPProvider, MockProvider, OpenAIResponsesProvider
from capability_factory.settings import Settings
from capability_factory.workflow import Workflow

PROJECT = Path(__file__).resolve().parents[1]
FIXTURE_SECRETS = ("fixture-deepseek-private", "fixture-openai-private", "fixture-local-private")


@pytest.fixture
def settings(tmp_path):
    # Construct settings directly so host environment and project .env cannot
    # make an offline test depend on a real account or remote model endpoint.
    return Settings(
        root=tmp_path, api_key=SecretStr(FIXTURE_SECRETS[0]),
        openai_api_key=SecretStr(FIXTURE_SECRETS[1]), local_api_key=SecretStr(FIXTURE_SECRETS[2]),
        openai_base_url="https://api.openai.com/v1", openai_model="gpt-5.5",
    )


def assert_secret_free(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    assert all(secret not in text for secret in FIXTURE_SECRETS)


@pytest.mark.parametrize("endpoint,deployment", [
    ("https://api.openai.com/v1", "official_api"),
    ("https://gateway.example/v1", "openai_compatible_api"),
])
def test_api_catalog_has_four_providers_and_safe_openai_metadata(settings, monkeypatch, endpoint, deployment):
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: pytest.fail("Catalog must not call an SDK endpoint"))
    application = create_app(settings.model_copy(update={"openai_base_url": endpoint}))
    with TestClient(application) as client:
        direct_response = client.get("/config/providers")
        full_response = client.get("/config")
        assert direct_response.status_code == full_response.status_code == 200
        direct = direct_response.json()
        assert full_response.json()["providers"] == direct
        providers = {item["id"]: item for item in direct["providers"]}
        assert set(providers) == {"deepseek", "openai", "local_http", "mock"}
        selected = providers["openai"]
        assert selected["configured"] is True
        assert selected["available"] is True
        assert selected["status"] == "configured"
        assert selected["deployment"] == deployment
        assert selected["api"] == "responses" and selected["sdk"] == "openai"
        assert selected["endpoint"] == endpoint
        assert selected["model"] == "gpt-5.5"
        assert direct["agent_runtime"]["framework"] == "langchain-core"
        assert direct["agent_runtime"]["external_tracing"] is False
        assert_secret_free(direct_response.text)
        assert_secret_free(full_response.text)


def test_api_missing_openai_key_keeps_option_visible_without_claiming_available(settings):
    application = create_app(settings.model_copy(update={"openai_api_key": SecretStr("")}))
    with TestClient(application) as client:
        catalog = client.get("/config/providers").json()
        selected = next(item for item in catalog["providers"] if item["id"] == "openai")
        assert selected["status"] == "missing_credentials"
        assert selected["configured"] is False
        assert selected["available"] is False
        assert selected["requires_api_key"] is True
        assert_secret_free(catalog)


@pytest.mark.parametrize("overrides", [
    {"openai_base_url": "http://api.openai.com/v1"},
    {"openai_base_url": "https://user:password@gateway.example/v1"},
    {"openai_base_url": "https://gateway.example/v1?token=fixture-openai-private"},
    {"openai_base_url": "https://gateway.example/v1#fragment"},
    {"openai_base_url": "https://gateway.example:invalid/v1"},
    {"openai_model": ""},
    {"openai_reasoning_effort": "invalid-effort"},
    {"openai_proxy_url": SecretStr("socks5://proxy-user:proxy-password@proxy.example:1080")},
])
def test_api_invalid_openai_configuration_is_unavailable_and_sanitized(settings, overrides):
    application = create_app(settings.model_copy(update=overrides))
    with TestClient(application) as client:
        response = client.get("/config/providers")
        assert response.status_code == 200
        selected = next(item for item in response.json()["providers"] if item["id"] == "openai")
        assert selected["configured"] is True
        assert selected["available"] is False
        assert selected["status"] == "invalid_configuration"
        assert selected["endpoint"] is None
        assert "password" not in response.text
        assert_secret_free(response.text)


def test_api_redacts_credentials_from_displayed_openai_model(settings):
    application = create_app(settings.model_copy(update={"openai_model": "model-" + "-".join(FIXTURE_SECRETS)}))
    with TestClient(application) as client:
        response = client.get("/config")
        assert response.status_code == 200
        selected = next(item for item in response.json()["providers"]["providers"] if item["id"] == "openai")
        assert selected["model"].count("[REDACTED]") == 3
        assert_secret_free(response.text)


def test_cli_init_missing_openai_key_exits_with_clear_message(settings, monkeypatch):
    missing = settings.model_copy(update={"openai_api_key": SecretStr("")})
    monkeypatch.setattr("capability_factory.cli.load_settings", lambda: missing)
    monkeypatch.setattr(KnowledgeStore, "ingest_sources", lambda *args, **kwargs: pytest.fail("Missing key must fail before extraction"))
    result = CliRunner().invoke(cli_app, ["init", "--provider", "openai"])
    assert result.exit_code == 1
    assert "OPENAI_API_KEY is missing" in result.output
    assert "Traceback" not in result.output
    assert isinstance(result.exception, SystemExit)
    assert_secret_free(result.output)


def test_cli_doctor_openai_discovers_models_with_safe_sdk_and_redacted_output(settings, monkeypatch):
    settings = settings.model_copy(update={
        "openai_base_url": "https://gateway.example/v1",
        "openai_model": "model-" + FIXTURE_SECRETS[1],
    })
    monkeypatch.setattr("capability_factory.cli.load_settings", lambda: settings)
    captured = {"model_calls": 0, "closed": False}

    def transport(**kwargs):
        captured["transport"] = kwargs
        return object()

    class Client:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.models = SimpleNamespace(list=self.list_models)

        def list_models(self):
            captured["model_calls"] += 1
            return SimpleNamespace(data=[
                SimpleNamespace(id="gpt-5.5"),
                SimpleNamespace(id="echo-" + "-".join(FIXTURE_SECRETS)),
            ])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            captured["closed"] = True

    monkeypatch.setattr(openai, "DefaultHttpxClient", transport)
    monkeypatch.setattr(openai, "OpenAI", Client)
    result = CliRunner().invoke(cli_app, ["doctor", "--provider", "openai", "--check-api"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["provider"] == "openai"
    assert data["api_status"] == "authenticated"
    assert data["deployment"] == "openai_compatible_api"
    assert data["model"] == "model-[REDACTED]"
    assert data["models"][0] == {"id": "gpt-5.5"}
    assert data["models"][1]["id"].count("[REDACTED]") == 3
    assert captured["model_calls"] == 1 and captured["closed"] is True
    assert captured["client"]["api_key"] == FIXTURE_SECRETS[1]
    assert captured["client"]["base_url"] == "https://gateway.example/v1"
    assert captured["client"]["max_retries"] == 0
    assert captured["transport"] == {"trust_env": False, "follow_redirects": False}
    assert_secret_free(result.output)


@pytest.mark.integration
def test_openai_langchain_sms_pipeline_uses_offline_fixture_and_real_validation(settings, monkeypatch):
    if not (PROJECT / "data/raw/SMSSpamCollection").is_file():
        pytest.skip("Run scripts/verify_data.py for the public SMS integration fixture")
    for directory in ("data", "docs", "configs"):
        (settings.root / directory).symlink_to(PROJECT / directory, target_is_directory=True)
    captured = []
    original_mock = MockProvider.generate

    def offline_generate(self, role, system, payload, **kwargs):
        # These deterministic replies verify wiring; they are never exported as
        # a paid API benchmark. Explicit fixture labels survive in every reply.
        assert isinstance(self, OpenAIResponsesProvider)
        assert self.mode == "openai"
        assert self.settings is not settings
        assert self.deadline is not None and self.checkpoint is not None
        self.checkpoint()
        captured.append({
            "role": role, "deadline": self.deadline,
            "timeout": self.settings.request_timeout_s, "model": self.model,
        })
        reply = original_mock(self, role, system, payload, **kwargs)
        if role == "interpreter":
            reply["assumptions"].append("OFFLINE_OPENAI_INTEGRATION_FIXTURE; no remote model invocation")
        elif role in {"coder", "repair_coder"}:
            reply["explanation"] = "OFFLINE_OPENAI_INTEGRATION_FIXTURE; deterministic constructor"
        return reply

    monkeypatch.setattr(OpenAIResponsesProvider, "generate", offline_generate)
    monkeypatch.setattr(HTTPProvider, "generate", lambda *args, **kwargs: pytest.fail("OpenAI must use the Responses provider"))
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: pytest.fail("Offline workflow fixture must not call the SDK"))
    report = Workflow(settings).run(RunRequest(
        description="OFFLINE_OPENAI_INTEGRATION_FIXTURE：识别短信垃圾信息，整个任务最多运行 120 秒，保存来源与验证报告。",
        provider="openai", dataset_id="sms", max_candidates=1, max_repairs=0, max_seconds=300,
    ))
    assert report["status"] == "passed", report.get("failure_reason")
    assert report["provider"] == "openai" and report["model"] == "gpt-5.5"
    assert report["provider_metadata"]["api"] == "responses"
    assert report["provider_metadata"]["store"] is False
    assert report["provenance"]["agent_runtime"]["framework"] == "langchain-core"
    assert report["provenance"]["agent_runtime"]["external_tracing"] is False
    assert report["provenance"]["sealed_test_scored"] is False
    assert [item["role"] for item in captured] == ["interpreter", "planner", "coder", "curator"]
    assert {item["model"] for item in captured} == {"gpt-5.5"}
    assert captured[0]["deadline"] - captured[1]["deadline"] == pytest.approx(180)
    assert len({item["deadline"] for item in captured[1:]}) == 1
    assert all(0 < item["timeout"] <= 120 for item in captured)
    assert report["timing"]["budget_seconds"] == 120
    assert report["timing"]["request_ceiling_seconds"] == 300
    retrieval = next(event for event in report["events"] if event["type"] == "KNOWLEDGE_RETRIEVED")
    assert retrieval["data"]["tool"] == "search_capabilities"
    assert retrieval["data"]["count"] == len(report["evidence"]) > 0
    candidate = report["candidates"][0]
    assert candidate["status"] == "passed"
    assert candidate["checks"]
    assert candidate["metrics"]["average_precision"] > candidate["metrics"]["dummy_average_precision"]
    assert candidate["resources"]["peak_rss_mib"] > 0
    assert "OFFLINE_OPENAI_INTEGRATION_FIXTURE" in candidate["explanation"]
    assert report["knowledge_writeback"]["run_saved"] is True
    persisted = KnowledgeStore(settings.db_path).get_run(report["run_id"])
    assert persisted["status"] == "passed"
    assert persisted["provenance"]["agent_runtime"] == report["provenance"]["agent_runtime"]
    for format_name in ("json", "html", "markdown"):
        assert Path(report["report_paths"][format_name]).is_file()
    saved = json.loads(Path(report["report_paths"]["json"]).read_text())
    assert saved["provider"] == "openai"
    assert saved["status"] == "passed"
    assert_secret_free(saved)
    role_audits = sorted((settings.runs_dir / report["run_id"] / "llm").glob("*.response.json"))
    assert len(role_audits) == 4
    assert any("OFFLINE_OPENAI_INTEGRATION_FIXTURE" in path.read_text() for path in role_audits)
