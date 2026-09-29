"""Provider contracts: authentic metadata, bounded retries and credential boundaries."""

import json

import httpx
import pytest
from pydantic import SecretStr

from capability_factory.providers import BudgetExceeded, HTTPProvider, ProviderError
from capability_factory.settings import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(root=tmp_path, api_key=SecretStr("fixture-credential"))


def response(content='{"ok":true}', status=200, finish="stop"):
    return httpx.Response(status, json={"id": "fixture-response", "model": "deepseek-flash", "system_fingerprint": "fixture",
                                       "choices": [{"message": {"content": content}, "finish_reason": finish}],
                                       "usage": {"prompt_tokens": 123, "completion_tokens": 20, "prompt_cache_hit_tokens": 10}})


def test_real_response_usage_and_hashes_are_recorded(monkeypatch, settings):
    captured = {}

    def post(url, **kwargs):
        captured.update(kwargs)
        return response()

    monkeypatch.setattr(httpx, "post", post)
    provider = HTTPProvider(settings)
    assert provider.generate("coder", "JSON", {"task": "example"}) == {"ok": True}
    assert provider.usage.input_tokens == 123
    assert provider.usage.output_tokens == 20
    assert provider.usage.cached_input_tokens == 10
    assert len(provider.usage.records[0]["response_sha256"]) == 64
    assert captured["trust_env"] is False
    assert captured["follow_redirects"] is False
    assert "fixture-credential" not in json.dumps(provider.usage.as_dict())
    assert "reasoning_content" not in json.dumps(provider.usage.as_dict())


@pytest.mark.parametrize("url", ["http://api.deepseek.com", "https://attacker.invalid", "https://api.deepseek.com@attacker.invalid", "https://user:password@api.deepseek.com"])
def test_credentials_never_sent_to_unapproved_host(settings, url):
    with pytest.raises(ProviderError):
        HTTPProvider(settings.model_copy(update={"base_url": url}))


def test_unauthorized_does_not_retry_or_fallback(monkeypatch, settings):
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: calls.append(1) or response(status=401))
    with pytest.raises(ProviderError, match="HTTP 401"):
        HTTPProvider(settings).generate("coder", "JSON", {})
    assert len(calls) == 1


def test_transient_retry_still_counts_budget(monkeypatch, settings):
    replies = iter([response(status=429), response()])
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: next(replies))
    monkeypatch.setattr("capability_factory.providers.time.sleep", lambda seconds: None)
    provider = HTTPProvider(settings)
    assert provider.generate("coder", "JSON", {})["ok"]
    assert provider.usage.calls == 2


@pytest.mark.parametrize("content,finish", [("not-json", "stop"), ("[]", "stop"), ('{"ok":true}', "length")])
def test_invalid_or_truncated_output_is_rejected(monkeypatch, settings, content, finish):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response(content, finish=finish))
    with pytest.raises(ProviderError):
        HTTPProvider(settings).generate("coder", "JSON", {})


def test_call_and_context_budget_checked_before_network(monkeypatch, settings):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: pytest.fail("Network must not be reached"))
    provider = HTTPProvider(settings.model_copy(update={"max_calls": 0}))
    with pytest.raises(BudgetExceeded):
        provider.generate("coder", "JSON", {})
    provider = HTTPProvider(settings.model_copy(update={"max_input_tokens": 1}))
    with pytest.raises(BudgetExceeded):
        provider.generate("coder", "JSON", {})


def test_local_provider_never_receives_deepseek_key(monkeypatch, settings):
    captured = {}
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: captured.update(kwargs) or response())
    HTTPProvider(settings, mode="local_http").generate("coder", "JSON", {})
    assert "Authorization" not in captured["headers"]


def test_local_provider_round_robins_four_replicas(monkeypatch, settings):
    urls = [
        "http://127.0.0.1:8100/v1",
        "http://127.0.0.1:8101/v1",
        "http://127.0.0.1:8102/v1",
        "http://127.0.0.1:8103/v1",
    ]
    settings = settings.model_copy(update={"local_base_urls": ",".join(urls), "local_model": "coder14"})
    calls = []
    monkeypatch.setattr(httpx, "post", lambda url, **kwargs: calls.append(url) or response())
    provider = HTTPProvider(settings, mode="local_http")
    provider.generate("coder", "JSON", {})
    provider.generate("coder", "JSON", {})
    assert calls == [urls[0] + "/chat/completions", urls[1] + "/chat/completions"]
    assert provider.metadata()["base_urls"] == urls


def test_retry_never_sends_request_after_absolute_deadline(monkeypatch, settings):
    clock = [100.0]
    calls = []

    def post(*args, **kwargs):
        calls.append(kwargs["timeout"])
        clock[0] = 111.0
        raise httpx.ReadTimeout("fixture")

    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setattr("capability_factory.providers.time.monotonic", lambda: clock[0])
    provider = HTTPProvider(settings)
    provider.deadline = 110.0
    with pytest.raises(BudgetExceeded, match="wall-clock"):
        provider.generate("coder", "JSON", {})
    assert calls == [10.0]
    assert provider.usage.calls == 1


def test_null_content_is_controlled_response_failure(monkeypatch, settings):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response(None))
    with pytest.raises(ProviderError, match="string"):
        HTTPProvider(settings).generate("coder", "JSON", {})
