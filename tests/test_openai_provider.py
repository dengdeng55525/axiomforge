"""Responses SDK contract tests use a local transport and incur no API costs."""

import hashlib
import json
from types import SimpleNamespace

import httpx
import openai
import pytest
from pydantic import SecretStr

from capability_factory.providers import (
    BudgetExceeded,
    OpenAIResponsesProvider,
    ProviderError,
    ResponseContractError,
)
from capability_factory.settings import Settings, load_settings


@pytest.fixture
def settings(tmp_path):
    return Settings(root=tmp_path, api_key=SecretStr("deepseek-fixture-secret"),
                    local_api_key=SecretStr("local-fixture-secret"),
                    openai_api_key=SecretStr("openai-fixture-secret"), openai_stream=False)


def response(content='{"ok":true}', status="completed", **overrides):
    values = {
        "id": "response-fixture", "model": "gpt-5.5", "status": status, "error": None,
        "output": [SimpleNamespace(type="message", role="assistant", status="completed",
                                   content=[SimpleNamespace(type="output_text", text=content)])],
        "usage": SimpleNamespace(input_tokens=21, output_tokens=7,
                                 input_tokens_details=SimpleNamespace(cached_tokens=8)),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def sdk(monkeypatch):
    captured = {"requests": [], "clients": [], "transports": [], "replies": [response()]}

    class Transport:
        def __init__(self, **kwargs):
            self.options = kwargs
            self.closed = False
            captured["transports"].append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

    class Client:
        def __init__(self, **kwargs):
            self.options = kwargs
            self.closed = False
            self.responses = SimpleNamespace(create=self.create)
            captured["clients"].append(self)

        def create(self, **kwargs):
            captured["requests"].append(kwargs)
            item = captured["replies"].pop(0)
            if isinstance(item, BaseException):
                raise item
            return item

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

    monkeypatch.setattr(openai, "DefaultHttpxClient", Transport)
    monkeypatch.setattr(openai, "OpenAI", Client)
    monkeypatch.setattr("capability_factory.providers.time.sleep", lambda seconds: None)
    return captured


def http_error(status):
    return openai.APIStatusError(
        "remote body includes openai-fixture-secret",
        response=httpx.Response(status, request=httpx.Request("POST", "https://gateway.invalid/v1/responses")),
        body={"message": "openai-fixture-secret"},
    )


def test_sdk_stateless_json_call_and_usage_are_audited(settings, sdk):
    events = []
    provider = OpenAIResponsesProvider(settings, lambda kind, data: events.append((kind, data)))
    assert provider.generate("planner", "Produce JSON", {"task": "中文分类"}) == {"ok": True}
    body = sdk["requests"][0]
    assert body["model"] == "gpt-5.5"
    assert body["store"] is False and body["stream"] is False
    assert body["text"] == {"format": {"type": "json_object"}}
    assert body["reasoning"] == {"effort": "none"}
    assert "previous_response_id" not in body
    assert body["input"][0] == {"role": "developer", "content": body["instructions"]}
    assert body["input"][1]["role"] == "user"
    assert body["input"][1]["content"].startswith("Task data (JSON):\n")
    assert json.loads(body["input"][1]["content"].split("\n", 1)[1]) == {"task": "中文分类"}
    assert sdk["clients"][0].options["max_retries"] == 0
    assert sdk["clients"][0].options["api_key"] == "openai-fixture-secret"
    assert sdk["transports"][0].options == {"trust_env": False, "follow_redirects": False, "timeout": 120}
    assert all(item.closed for item in sdk["clients"] + sdk["transports"])
    usage = provider.usage.as_dict()
    assert (usage["calls"], usage["input_tokens"], usage["output_tokens"], usage["cached_input_tokens"]) == (1, 21, 7, 8)
    assert len(usage["records"][0]["prompt_sha256"]) == 64
    expected_hash = hashlib.sha256(json.dumps(
        {"instructions": body["instructions"], "input": body["input"]},
        ensure_ascii=False, sort_keys=True,
    ).encode()).hexdigest()
    assert usage["records"][0]["prompt_sha256"] == expected_hash
    assert len(usage["records"][0]["response_sha256"]) == 64
    assert usage["records"][0]["api"] == "responses"
    assert usage["records"][0]["requested_max_output_tokens"] == 4096
    assert usage["records"][0]["output_limit_exceeded"] is False
    assert usage["records"][0]["stream"] is False
    assert events[0][0] == "LLM_RESPONSE"
    serialized = json.dumps({"usage": usage, "metadata": provider.metadata(), "events": events})
    assert "fixture-secret" not in serialized


@pytest.mark.parametrize("url", [
    "http://api.openai.com/v1", "https:///v1", "https://user:password@example.com/v1",
    "https://example.com/v1?key=x", "https://example.com/v1#fragment",
    "https://example.com/v1?", "https://example.com/v1#",
    "https://example.com:invalid/v1", "https://exa mple.com/v1",
    "https://example.com/openai-fixture-secret",
])
def test_rejects_unsafe_or_invalid_endpoint(settings, url):
    with pytest.raises(ProviderError):
        OpenAIResponsesProvider(settings.model_copy(update={"openai_base_url": url}))


def test_official_and_custom_endpoints_are_explicit(settings):
    official = OpenAIResponsesProvider(settings).metadata()
    assert official["deployment"] == "official_api"
    custom = OpenAIResponsesProvider(settings.model_copy(update={
        "openai_base_url": "https://gateway.example/v1/", "openai_model": "operator-model",
    })).metadata()
    assert custom["deployment"] == "openai_compatible_api"
    assert custom["model"] == "operator-model"
    assert custom["base_url"] == "https://gateway.example/v1"
    assert custom["store"] is False


@pytest.mark.parametrize("overrides", [
    {"openai_api_key": SecretStr("")}, {"openai_model": " "},
    {"openai_reasoning_effort": "invented"},
])
def test_required_configuration_is_validated(settings, overrides):
    with pytest.raises(ProviderError):
        OpenAIResponsesProvider(settings.model_copy(update=overrides))


def test_model_default_reasoning_omits_field(settings, sdk):
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_reasoning_effort": ""}))
    provider.generate("coder", "JSON", {})
    assert "reasoning" not in sdk["requests"][0]


@pytest.mark.parametrize("proxy", [
    "http://127.0.0.1:7890",
    "https://proxy-user:proxy-password@proxy.example:8443",
])
def test_explicit_proxy_is_sent_only_to_transport_and_hidden_from_metadata(settings, sdk, proxy):
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_proxy_url": SecretStr(proxy)}))
    provider.generate("coder", "JSON", {})
    assert sdk["transports"][0].options["proxy"] == proxy
    assert sdk["transports"][0].options["trust_env"] is False
    assert sdk["transports"][0].options["follow_redirects"] is False
    metadata = provider.metadata()
    assert metadata["proxy_configured"] is True
    assert "proxy_url" not in metadata
    audit = json.dumps({"metadata": metadata, "usage": provider.usage.as_dict()})
    assert proxy not in audit
    assert "proxy-password" not in audit
    assert "proxy-user" not in audit
    assert proxy not in json.dumps(sdk["requests"])
    assert proxy not in repr(provider.settings)


def test_empty_proxy_ignores_environment_proxy(settings, sdk, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://ambient-proxy.example:8080")
    provider = OpenAIResponsesProvider(settings)
    provider.generate("coder", "JSON", {})
    assert "proxy" not in sdk["transports"][0].options
    assert sdk["transports"][0].options["trust_env"] is False
    assert provider.metadata()["proxy_configured"] is False


@pytest.mark.parametrize("proxy", [
    "socks5://proxy.example:1080", "file:///tmp/proxy", "http:///missing-host",
    "http://proxy.example:bad", "http://proxy.example:8080?password=secret",
    "https://proxy.example:8443#fragment", "http://proxy.example:8080?",
    "http://proxy.example:8080#", "http://proxy example:8080",
])
def test_invalid_proxy_is_rejected_without_leaking_configuration(settings, sdk, proxy):
    with pytest.raises(ProviderError, match="proxy") as raised:
        OpenAIResponsesProvider(settings.model_copy(update={"openai_proxy_url": SecretStr(proxy)}))
    assert proxy not in str(raised.value)
    assert not sdk["requests"]


def test_proxy_url_and_encoded_credentials_are_redacted_from_sdk_metadata(settings, sdk):
    proxy = "http://proxy%2Duser:proxy%2Dpassword@proxy.example:8080"
    remote = response()
    remote.id = "echo-" + proxy
    remote.model = "proxy-user:proxy-password;proxy%2Duser:proxy%2Dpassword"
    sdk["replies"] = [remote]
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_proxy_url": SecretStr(proxy)}))
    provider.generate("coder", "JSON", {})
    audit = json.dumps(provider.usage.as_dict())
    assert proxy not in audit
    assert "proxy-user" not in audit and "proxy%2Duser" not in audit
    assert "proxy-password" not in audit and "proxy%2Dpassword" not in audit
    assert "[REDACTED]" in audit


@pytest.mark.parametrize("status", [301, 302, 307, 400, 401, 403, 404])
def test_nontransient_http_failure_is_sanitized_without_retry(settings, sdk, status):
    sdk["replies"] = [http_error(status)]
    with pytest.raises(ProviderError, match=f"HTTP {status}") as raised:
        OpenAIResponsesProvider(settings).generate("coder", "JSON", {})
    assert "fixture-secret" not in str(raised.value)
    assert len(sdk["requests"]) == 1
    assert all(item.closed for item in sdk["clients"] + sdk["transports"])


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_retry_is_explicit_and_counts_budget(settings, sdk, status):
    sdk["replies"] = [http_error(status), response()]
    provider = OpenAIResponsesProvider(settings)
    assert provider.generate("coder", "JSON", {}) == {"ok": True}
    assert provider.usage.calls == 2
    assert len(sdk["clients"]) == 2
    assert all(item.options["max_retries"] == 0 for item in sdk["clients"])
    assert all(item["model"] == "gpt-5.5" for item in sdk["requests"])


def test_transport_retry_is_bounded_and_sanitized(settings, sdk):
    error = openai.APIConnectionError(
        message="transport leaked openai-fixture-secret", request=httpx.Request("POST", "https://gateway.invalid"),
    )
    sdk["replies"] = [error, error]
    provider = OpenAIResponsesProvider(settings)
    with pytest.raises(ProviderError, match="APIConnectionError") as raised:
        provider.generate("coder", "JSON", {})
    assert provider.usage.calls == 2
    assert "fixture-secret" not in str(raised.value)
    assert all(item.closed for item in sdk["clients"] + sdk["transports"])


@pytest.mark.parametrize("overrides", [
    {"max_calls": 0}, {"max_input_tokens": 1}, {"max_output_tokens": 255},
])
def test_exhausted_budgets_prevent_sdk_call(settings, sdk, overrides):
    provider = OpenAIResponsesProvider(settings.model_copy(update=overrides))
    with pytest.raises(BudgetExceeded):
        provider.generate("coder", "JSON", {})
    assert not sdk["requests"]


@pytest.mark.parametrize("remaining_delta", [-1, 0])
def test_json_input_envelope_is_included_in_conservative_budget(settings, sdk, remaining_delta):
    system = "Produce a result"
    payload = {"task": "中文短信"}
    instructions = system + "\nReturn exactly one JSON object. Never include private reasoning, secrets or markdown fences."
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    expected_input = [
        {"role": "developer", "content": instructions},
        {"role": "user", "content": "Task data (JSON):\n" + serialized},
    ]
    required = len(json.dumps(
        {"instructions": instructions, "input": expected_input},
        ensure_ascii=False, sort_keys=True,
    ).encode("utf-8")) + 128
    # Previously billed tokens count toward the same ceiling as this full
    # input, including its compatibility envelope and multibyte task text.
    provider = OpenAIResponsesProvider(settings.model_copy(update={
        "max_input_tokens": required + 37 + remaining_delta,
    }))
    provider.usage.input_tokens = 37
    if remaining_delta < 0:
        with pytest.raises(BudgetExceeded, match="input-token budget"):
            provider.generate("coder", system, payload)
        assert not sdk["requests"]
        assert provider.usage.calls == 0
    else:
        assert provider.generate("coder", system, payload) == {"ok": True}
        assert sdk["requests"][0]["input"] == expected_input
        assert provider.usage.calls == 1


def test_remaining_output_and_deadline_cap_request(settings, sdk, monkeypatch):
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: 100.0)
    provider = OpenAIResponsesProvider(settings.model_copy(update={"max_output_tokens": 500}))
    provider.usage.output_tokens = 200
    provider.deadline = 108.5
    provider.generate("coder", "JSON", {}, max_tokens=900)
    assert sdk["requests"][0]["max_output_tokens"] == 300
    assert sdk["requests"][0]["timeout"] == 8.5
    assert sdk["clients"][0].options["timeout"] == 8.5


def test_retry_stops_when_call_budget_is_exhausted(settings, sdk):
    sdk["replies"] = [http_error(429)]
    provider = OpenAIResponsesProvider(settings.model_copy(update={"max_calls": 1}))
    with pytest.raises(BudgetExceeded):
        provider.generate("coder", "JSON", {})
    assert len(sdk["requests"]) == 1


def test_retry_stops_after_deadline(settings, sdk, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: clock[0])
    error = http_error(429)

    class AdvancingErrorReply(list):
        def pop(self, index=0):
            clock[0] = 110.0
            return error

    sdk["replies"] = AdvancingErrorReply([error])
    provider = OpenAIResponsesProvider(settings)
    provider.deadline = 105.0
    with pytest.raises(BudgetExceeded, match="wall-clock"):
        provider.generate("coder", "JSON", {})
    assert len(sdk["requests"]) == 1


def test_expired_deadline_prevents_sdk_call(settings, sdk, monkeypatch):
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: 10.0)
    provider = OpenAIResponsesProvider(settings)
    provider.deadline = 10.0
    with pytest.raises(BudgetExceeded, match="wall-clock"):
        provider.generate("coder", "JSON", {})
    assert not sdk["requests"]
    assert provider.usage.calls == 0


def test_deadline_expiring_during_response_keeps_billed_usage(settings, sdk, monkeypatch):
    clock = [10.0]
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: clock[0])

    class LateReply(list):
        def pop(self, index=0):
            clock[0] = 30.0
            return response()

    sdk["replies"] = LateReply([response()])
    provider = OpenAIResponsesProvider(settings)
    provider.deadline = 20.0
    with pytest.raises(BudgetExceeded, match="wall-clock"):
        provider.generate("coder", "JSON", {})
    assert provider.usage.input_tokens == 21
    assert provider.usage.output_tokens == 7
    assert len(sdk["requests"]) == 1


@pytest.mark.parametrize("field,value", [("input_tokens", 200001), ("output_tokens", 40001)])
def test_unexpected_upstream_token_overrun_is_recorded_and_fails(settings, sdk, field, value):
    remote = response()
    setattr(remote.usage, field, value)
    sdk["replies"] = [remote]
    provider = OpenAIResponsesProvider(settings)
    with pytest.raises(BudgetExceeded, match="token budget"):
        provider.generate("coder", "JSON", {})
    assert getattr(provider.usage, field) == value
    assert provider.usage.records[0][field] == value


def test_checkpoint_cancellation_prevents_sdk_call(settings, sdk):
    provider = OpenAIResponsesProvider(settings)

    def cancelled():
        raise RuntimeError("cancelled")

    provider.checkpoint = cancelled
    with pytest.raises(RuntimeError, match="cancelled"):
        provider.generate("coder", "JSON", {})
    assert not sdk["requests"]


@pytest.mark.parametrize("remote", [
    response(content="not JSON"), response(content="[]"), response(content=""),
    response(status="incomplete"), response(status="failed"), response(status=None),
    response(error=SimpleNamespace(message="server failure")),
    response(output=[SimpleNamespace(type="function_call", arguments="{}")]),
    response(output=[SimpleNamespace(type="message", role="assistant", status="incomplete",
                                     content=[SimpleNamespace(type="output_text", text='{"ok":true}')])]),
])
def test_invalid_or_incomplete_output_keeps_usage_and_rejects_content(settings, sdk, remote):
    sdk["replies"] = [remote]
    provider = OpenAIResponsesProvider(settings)
    with pytest.raises(ResponseContractError):
        provider.generate("coder", "JSON", {})
    assert provider.usage.calls == 1
    assert provider.usage.input_tokens == 21
    assert len(provider.usage.records) == 1


def test_refusal_does_not_leak_text_or_recall_model(settings, sdk):
    sdk["replies"] = [response(output=[SimpleNamespace(
        type="message", role="assistant", status="completed",
        content=[SimpleNamespace(type="refusal", refusal="private refusal detail")],
    )])]
    provider = OpenAIResponsesProvider(settings)
    with pytest.raises(ProviderError, match="declined") as raised:
        provider.generate("coder", "JSON", {})
    assert not isinstance(raised.value, ResponseContractError)
    assert "private refusal" not in json.dumps(provider.usage.as_dict())
    assert len(sdk["requests"]) == 1


@pytest.mark.parametrize("usage", [
    None, SimpleNamespace(input_tokens=None, output_tokens=3),
    SimpleNamespace(input_tokens=3, output_tokens=-1),
    SimpleNamespace(input_tokens=True, output_tokens=3),
    SimpleNamespace(input_tokens=3, output_tokens=1.5),
    SimpleNamespace(input_tokens=3, output_tokens=1, input_tokens_details=SimpleNamespace(cached_tokens=4)),
])
def test_missing_or_invalid_usage_blocks_further_spending(settings, sdk, usage):
    sdk["replies"] = [response(usage=usage)]
    provider = OpenAIResponsesProvider(settings)
    with pytest.raises(ProviderError, match="usage|token counts"):
        provider.generate("coder", "JSON", {})
    assert provider.usage.records[0]["usage_available"] is False
    assert provider.usage.records[0]["input_tokens"] is None
    with pytest.raises(BudgetExceeded, match="unavailable"):
        provider.generate("coder", "JSON", {})
    assert len(sdk["requests"]) == 1


def test_reasoning_content_and_credential_echo_are_not_saved(settings, sdk):
    remote = response()
    remote.output.insert(0, SimpleNamespace(type="reasoning", summary="private chain of thought"))
    remote.id = "response-openai-fixture-secret"
    remote.model = "model-deepseek-fixture-secret"
    sdk["replies"] = [remote]
    provider = OpenAIResponsesProvider(settings)
    assert provider.generate("coder", "JSON", {}) == {"ok": True}
    audit = json.dumps(provider.usage.as_dict())
    assert "fixture-secret" not in audit
    assert "private chain of thought" not in audit
    assert "[REDACTED]" in audit


def test_configuration_reads_server_secrets_and_preserves_empty_reasoning(tmp_path, monkeypatch):
    for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_REASONING_EFFORT", "OPENAI_PROXY_URL", "OPENAI_STREAM"):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=file-secret\nOPENAI_BASE_URL=https://gateway.example/v1\n"
        "OPENAI_MODEL=model-from-file\nOPENAI_REASONING_EFFORT=\n"
        "OPENAI_PROXY_URL=http://proxy-user:proxy-password@proxy.example:8080\n",
    )
    settings = load_settings(tmp_path)
    assert isinstance(settings.openai_api_key, SecretStr)
    assert settings.openai_api_key.get_secret_value() == "file-secret"
    assert settings.openai_base_url == "https://gateway.example/v1"
    assert settings.openai_model == "model-from-file"
    assert settings.openai_reasoning_effort == ""
    assert isinstance(settings.openai_proxy_url, SecretStr)
    assert settings.openai_proxy_url.get_secret_value() == "http://proxy-user:proxy-password@proxy.example:8080"
    assert "file-secret" not in repr(settings)
    assert "proxy-password" not in repr(settings)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")
    monkeypatch.setenv("OPENAI_PROXY_URL", "")
    assert load_settings(tmp_path).openai_api_key.get_secret_value() == "environment-secret"
    assert load_settings(tmp_path).openai_model == "gpt-5.5"
    assert load_settings(tmp_path).openai_proxy_url.get_secret_value() == ""


def test_actual_sdk_posts_responses_with_closed_transport(settings, monkeypatch):
    # Official SDK 3.x uses httpx2; 2.x uses httpx. The SDK transport itself
    # selects the matching implementation, and this fixture mirrors it.
    transport_module = openai.DefaultHttpxClient.__mro__[1].__module__.split(".")[0]
    import importlib

    http = importlib.import_module(transport_module)
    requests = []
    clients = []
    original = openai.DefaultHttpxClient

    def respond(request):
        requests.append(request)
        return http.Response(200, json={
            "id": "real-sdk-fixture", "object": "response", "created_at": 1,
            "model": "gpt-5.5", "status": "completed", "error": None,
            "output": [{"id": "message-fixture", "type": "message", "role": "assistant",
                        "status": "completed", "content": [{"type": "output_text",
                        "text": '{"ok":true}', "annotations": []}]}],
            "usage": {"input_tokens": 21, "output_tokens": 7, "total_tokens": 28,
                      "input_tokens_details": {"cached_tokens": 8},
                      "output_tokens_details": {"reasoning_tokens": 0}},
        })

    def transport(**kwargs):
        client = original(transport=http.MockTransport(respond), **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(openai, "DefaultHttpxClient", transport)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    provider = OpenAIResponsesProvider(settings)
    payload = {"task": "短信垃圾分类", "features": ["text"], "limit": 2, "enabled": True}
    assert provider.generate("coder", "JSON", payload) == {"ok": True}
    assert str(requests[0].url) == "https://api.openai.com/v1/responses"
    assert requests[0].headers["authorization"] == "Bearer openai-fixture-secret"
    body = json.loads(requests[0].content)
    assert body["store"] is False
    assert body["model"] == "gpt-5.5"
    assert body["input"][0] == {"role": "developer", "content": body["instructions"]}
    assert body["input"][1]["role"] == "user"
    user_input = body["input"][1]["content"]
    assert "json" in user_input.lower()
    assert user_input.startswith("Task data (JSON):\n")
    assert json.loads(user_input.split("\n", 1)[1]) == payload
    assert len(requests) == 1
    assert clients[0].is_closed
    assert clients[0].follow_redirects is False
    assert clients[0]._trust_env is False


def test_actual_sdk_does_not_forward_credentials_on_redirect(settings, monkeypatch):
    import importlib

    http = importlib.import_module(openai.DefaultHttpxClient.__mro__[1].__module__.split(".")[0])
    original = openai.DefaultHttpxClient
    requests = []
    clients = []

    def redirect(request):
        requests.append(request)
        return http.Response(307, headers={"location": "https://unapproved.invalid/responses"})

    def transport(**kwargs):
        client = original(transport=http.MockTransport(redirect), **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(openai, "DefaultHttpxClient", transport)
    provider = OpenAIResponsesProvider(settings)
    with pytest.raises(ProviderError, match="HTTP 307"):
        provider.generate("coder", "JSON", {})
    assert len(requests) == 1
    assert requests[0].url.host == "api.openai.com"
    assert clients[0].is_closed


@pytest.mark.parametrize("environment,expected", [(None, True), ("true", True), ("false", False), ("0", False)])
def test_streaming_defaults_on_and_supports_explicit_environment_override(tmp_path, monkeypatch, environment, expected):
    monkeypatch.delenv("OPENAI_STREAM", raising=False)
    if environment is not None:
        monkeypatch.setenv("OPENAI_STREAM", environment)
    assert Settings(root=tmp_path).openai_stream is True
    assert load_settings(tmp_path).openai_stream is expected


def test_upstream_per_call_output_overrun_is_explicit_in_usage(settings, sdk):
    remote = response()
    remote.usage.output_tokens = 2057
    sdk["replies"] = [remote]
    provider = OpenAIResponsesProvider(settings)
    assert provider.generate("interpreter", "JSON", {}, max_tokens=1300) == {"ok": True}
    assert sdk["requests"][0]["max_output_tokens"] == 1300
    assert provider.usage.output_tokens == 2057
    record = provider.usage.records[0]
    assert record["requested_max_output_tokens"] == 1300
    assert record["output_limit_exceeded"] is True


def test_output_overrun_still_enforces_real_global_usage(settings, sdk):
    remote = response()
    remote.usage.output_tokens = 500
    sdk["replies"] = [remote]
    provider = OpenAIResponsesProvider(settings.model_copy(update={"max_output_tokens": 1000}))
    provider.usage.output_tokens = 700
    with pytest.raises(BudgetExceeded, match="output-token budget"):
        provider.generate("coder", "JSON", {}, max_tokens=1000)
    assert sdk["requests"][0]["max_output_tokens"] == 300
    assert provider.usage.output_tokens == 1200
    assert provider.usage.records[0]["requested_max_output_tokens"] == 300
    assert provider.usage.records[0]["output_limit_exceeded"] is True


def stream_response(status="completed"):
    return {
        "id": "sse-response-fixture", "object": "response", "created_at": 1,
        "model": "gpt-5.5", "status": status, "error": None,
        "output": [
            {"type": "reasoning", "id": "reasoning-fixture",
             "summary": [{"type": "summary_text", "text": "PRIVATE_REASONING_FIXTURE"}]},
            {"id": "message-fixture", "type": "message", "role": "assistant",
             "status": "completed", "content": [
                 {"type": "output_text", "text": '{"ok":true}', "annotations": []},
             ]},
        ],
        "usage": {"input_tokens": 21, "output_tokens": 7, "total_tokens": 28,
                  "input_tokens_details": {"cached_tokens": 8},
                  "output_tokens_details": {"reasoning_tokens": 3}},
    }


@pytest.fixture
def sse_sdk(monkeypatch):
    """Exercise the actual official SDK SSE parser with an in-memory stream."""
    import importlib

    http = importlib.import_module(openai.DefaultHttpxClient.__mro__[1].__module__.split(".")[0])
    original = openai.DefaultHttpxClient
    captured = {
        "requests": [], "clients": [], "emitted": [], "closed": False, "event_hook": None,
        "events": [
            {"type": "response.created", "response": stream_response("in_progress")},
            {"type": "response.reasoning_text.delta", "delta": "PRIVATE_REASONING_FIXTURE"},
            {"type": "codex.rate_limits", "limits": "PRIVATE_CODEX_METADATA_FIXTURE"},
            {"type": "response.output_text.delta", "delta": "PARTIAL_UNTRUSTED_OUTPUT_FIXTURE"},
            {"type": "response.completed", "response": stream_response()},
        ],
    }

    class Body(http.SyncByteStream):
        def __iter__(self):
            for index, event in enumerate(captured["events"]):
                if captured["event_hook"] is not None:
                    captured["event_hook"](index, event)
                captured["emitted"].append(event["type"])
                payload = json.dumps({"sequence_number": index, **event})
                yield ("event: " + event["type"] + "\ndata: " + payload + "\n\n").encode()
            yield b"data: [DONE]\n\n"

        def close(self):
            captured["closed"] = True

    def respond(request):
        captured["requests"].append(request)
        return http.Response(200, headers={"content-type": "text/event-stream"}, stream=Body())

    def transport(**kwargs):
        client = original(transport=http.MockTransport(respond), **kwargs)
        captured["clients"].append(client)
        return client

    monkeypatch.setattr(openai, "DefaultHttpxClient", transport)
    return captured


def test_actual_sdk_stream_uses_typed_inputs_and_only_terminal_json(settings, sse_sdk):
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    checkpoint_calls = []
    provider.checkpoint = lambda: checkpoint_calls.append(True)
    payload = {"task": "短信分类", "limit": 2}
    assert provider.generate("interpreter", "Produce JSON", payload) == {"ok": True}
    assert provider.metadata()["stream"] is True
    body = json.loads(sse_sdk["requests"][0].content)
    assert body["stream"] is True and body["store"] is False
    assert body["input"][0] == {"role": "developer", "content": body["instructions"]}
    assert body["input"][1]["role"] == "user"
    assert json.loads(body["input"][1]["content"].split("\n", 1)[1]) == payload
    assert provider.usage.calls == 1
    assert provider.usage.input_tokens == 21 and provider.usage.output_tokens == 7
    assert len(provider.usage.records) == 1
    assert len(checkpoint_calls) >= 5
    record = provider.usage.records[0]
    assert record["stream"] is True
    expected_hash = hashlib.sha256(json.dumps(
        {"instructions": body["instructions"], "input": body["input"]},
        ensure_ascii=False, sort_keys=True,
    ).encode()).hexdigest()
    assert record["prompt_sha256"] == expected_hash
    audit = json.dumps(provider.usage.as_dict())
    assert "PRIVATE_REASONING_FIXTURE" not in audit
    assert "PRIVATE_CODEX_METADATA_FIXTURE" not in audit
    assert "PARTIAL_UNTRUSTED_OUTPUT_FIXTURE" not in audit
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])


def test_actual_sdk_stream_without_terminal_rejects_partial_and_blocks_spend(settings, sse_sdk):
    sse_sdk["events"].pop()
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    with pytest.raises(ResponseContractError, match="without a terminal response"):
        provider.generate("coder", "JSON", {})
    assert provider.usage.calls == 1
    assert provider.usage.records == []
    with pytest.raises(BudgetExceeded, match="unavailable"):
        provider.generate("coder", "JSON", {})
    assert len(sse_sdk["requests"]) == 1
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])


@pytest.mark.parametrize("terminal", ["incomplete", "failed"])
def test_actual_sdk_stream_terminal_failure_preserves_usage(settings, sse_sdk, terminal):
    sse_sdk["events"][-1] = {"type": "response." + terminal, "response": stream_response(terminal)}
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    with pytest.raises(ResponseContractError, match="incomplete or failed"):
        provider.generate("coder", "JSON", {})
    assert provider.usage.calls == 1
    assert provider.usage.output_tokens == 7
    assert provider.usage.records[0]["finish_reason"] == terminal
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])


def test_actual_sdk_stream_cancellation_closes_resources_before_completion(settings, sse_sdk):
    cancelled = [False]

    def on_event(index, event):
        if index == 1:
            cancelled[0] = True

    def checkpoint():
        if cancelled[0]:
            raise RuntimeError("fixture cancellation")

    sse_sdk["event_hook"] = on_event
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    provider.checkpoint = checkpoint
    with pytest.raises(RuntimeError, match="fixture cancellation"):
        provider.generate("coder", "JSON", {})
    assert "response.completed" not in sse_sdk["emitted"]
    assert provider.usage.records == []
    assert len(sse_sdk["requests"]) == 1
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])


def test_actual_sdk_stream_checks_deadline_between_events(settings, sse_sdk, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: clock[0])

    def on_event(index, event):
        if index == 1:
            clock[0] = 121.0

    sse_sdk["event_hook"] = on_event
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    provider.deadline = 120.0
    with pytest.raises(BudgetExceeded, match="wall-clock"):
        provider.generate("coder", "JSON", {})
    assert "response.completed" not in sse_sdk["emitted"]
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])


def test_actual_sdk_late_stream_terminal_accounts_usage_before_timeout(settings, sse_sdk, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: clock[0])
    sse_sdk["events"] = [{"type": "response.completed", "response": stream_response()}]
    sse_sdk["event_hook"] = lambda *args: clock.__setitem__(0, 121.0)
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    provider.deadline = 120.0
    provider.checkpoint = lambda: None
    with pytest.raises(BudgetExceeded, match="wall-clock"):
        provider.generate("coder", "JSON", {})
    assert provider.usage.input_tokens == 21
    assert provider.usage.output_tokens == 7
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])


def test_actual_sdk_stream_transport_failure_does_not_retry_or_expose_payload(settings, sse_sdk):
    def break_stream(index, event):
        if index == 1:
            raise RuntimeError("remote body openai-fixture-secret proxy-password")

    sse_sdk["event_hook"] = break_stream
    provider = OpenAIResponsesProvider(settings.model_copy(update={"openai_stream": True}))
    with pytest.raises(ProviderError, match="stream transport failure") as raised:
        provider.generate("coder", "JSON", {})
    assert "fixture-secret" not in str(raised.value)
    assert "proxy-password" not in str(raised.value)
    assert provider.usage.calls == 1
    assert sse_sdk["closed"] is True
    assert all(client.is_closed for client in sse_sdk["clients"])
