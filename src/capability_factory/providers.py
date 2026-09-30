"""Budgeted HTTP inference, explicit mock mode, no silent provider fallback."""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import unquote, urlparse

import httpx

from capability_factory.settings import Settings


class ProviderError(RuntimeError):
    """Sanitized remote or response-contract failure."""


class BudgetExceeded(ProviderError):
    pass


class ResponseContractError(ProviderError):
    """A completed response can be retried once with a format correction."""


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    records: list[dict] = field(default_factory=list)

    def as_dict(self):
        return {"calls": self.calls, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "cached_input_tokens": self.cached_input_tokens, "records": list(self.records)}


class HTTPProvider:
    def __init__(self, settings: Settings, mode="deepseek", event_callback: Callable | None = None):
        if mode not in {"deepseek", "local_http"}:
            raise ProviderError("Unsupported HTTP provider mode")
        self.settings = settings
        self.mode = mode
        self.usage = Usage()
        self.event_callback = event_callback
        self.deadline = None
        self.checkpoint = None
        self.model = settings.model if mode == "deepseek" else settings.local_model
        self.base_urls = ([settings.base_url.rstrip("/")] if mode == "deepseek" else settings.local_endpoints)
        if not self.base_urls or any(not value for value in self.base_urls):
            raise ProviderError("Provider URL is empty")
        self._endpoint_index = 0
        for endpoint in self.base_urls:
            parsed = urlparse(endpoint)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ProviderError("Provider URL must use HTTP(S) and include a host")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ProviderError("Provider URL must not contain credentials, query, or fragment")
            if mode == "deepseek" and (parsed.scheme != "https" or parsed.hostname != "api.deepseek.com"):
                raise ProviderError("DeepSeek credentials can only be sent to the official HTTPS host")
        if mode == "deepseek" and not settings.api_key.get_secret_value():
            raise ProviderError("DEEPSEEK_API_KEY is missing; configure an uncommitted .env or environment")
        if mode == "local_http" and len(self.base_urls) > 1 and not settings.local_model:
            raise ProviderError("LOCAL_LLM_MODEL is required when using a local endpoint pool")

    def metadata(self) -> dict:
        """Return UI-safe connection metadata without credentials or prompts."""

        return {
            "provider": self.mode,
            "model": self.model,
            "base_url": self.base_urls[0],
            "base_urls": list(self.base_urls),
            "authorization": "bearer" if self.mode == "deepseek" or self.settings.local_api_key.get_secret_value() else "none",
            "local_profile": self.settings.local_profile if self.mode == "local_http" else None,
            "deployment": "official_api" if self.mode == "deepseek" else "external_local_http",
        }

    def generate(self, role, system, payload, max_tokens=4096):
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if len(serialized) > 120000:
            raise BudgetExceeded("Context exceeds application payload size limit")
        if self.usage.calls >= self.settings.max_calls:
            raise BudgetExceeded("LLM call budget exhausted")
        if self.usage.input_tokens >= self.settings.max_input_tokens:
            raise BudgetExceeded("LLM input token budget exhausted")
        conservative_input_bound = len((system + serialized).encode("utf-8")) + 128
        if self.usage.input_tokens + conservative_input_bound > self.settings.max_input_tokens:
            raise BudgetExceeded("Request cannot fit remaining conservative input-token budget")
        remaining = self.settings.max_output_tokens - self.usage.output_tokens
        if remaining < 256:
            raise BudgetExceeded("LLM output token budget exhausted")
        max_tokens = min(max_tokens, remaining)
        messages = [
            {"role": "system", "content": system + "\nReturn exactly one JSON object. Never include private reasoning, secrets or markdown fences."},
            {"role": "user", "content": serialized},
        ]
        body = {"model": self.model, "messages": messages, "stream": False,
                "response_format": {"type": "json_object"}, "max_tokens": max_tokens, "temperature": 0}
        if self.mode == "deepseek":
            body["thinking"] = {"type": "disabled"}
        headers = {"Content-Type": "application/json", "User-Agent": "AlgoForge/0.1"}
        if self.mode == "deepseek":
            headers["Authorization"] = "Bearer " + self.settings.api_key.get_secret_value()
        elif self.settings.local_api_key.get_secret_value():
            headers["Authorization"] = "Bearer " + self.settings.local_api_key.get_secret_value()
        prompt_hash = hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode()).hexdigest()
        for attempt in range(2):
            if self.checkpoint:
                self.checkpoint()
            timeout = self.settings.request_timeout_s
            if self.deadline is not None:
                remaining_seconds = self.deadline - time.monotonic()
                if remaining_seconds <= 0:
                    raise BudgetExceeded("Run wall-clock budget exhausted before HTTP request")
                timeout = min(timeout, remaining_seconds)
            if self.usage.calls >= self.settings.max_calls:
                raise BudgetExceeded("LLM call budget exhausted during retry")
            self.usage.calls += 1
            started = time.monotonic()
            endpoint = self.base_urls[self._endpoint_index % len(self.base_urls)]
            # Advance before issuing the request so a failed replica moves to
            # the next one and concurrent provider instances naturally share
            # the pool without requiring a central load balancer.
            self._endpoint_index = (self._endpoint_index + 1) % len(self.base_urls)
            try:
                response = httpx.post(endpoint + "/chat/completions", headers=headers, json=body,
                                      timeout=timeout, follow_redirects=False, trust_env=False)
            except httpx.TransportError as error:
                if attempt == 0:
                    self._retry_pause()
                    continue
                raise ProviderError(f"Provider transport failure: {type(error).__name__}") from None
            if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                self._retry_pause()
                continue
            if response.status_code != 200:
                raise ProviderError(f"Provider returned HTTP {response.status_code}; no automatic model substitution")
            try:
                remote = response.json()
                usage = remote.get("usage", {})
                input_count = int(usage.get("prompt_tokens", 0))
                output_count = int(usage.get("completion_tokens", 0))
                self.usage.input_tokens += input_count
                self.usage.output_tokens += output_count
                self.usage.cached_input_tokens += int(usage.get("prompt_cache_hit_tokens", 0))
                choice = remote["choices"][0]
                content = choice["message"]["content"]
                if not isinstance(content, str):
                    raise ResponseContractError("Provider response content must be a string")
                record = {"role": role, "requested_model": self.model, "returned_model": remote.get("model"),
                          "endpoint": endpoint,
                          "response_id": remote.get("id"), "system_fingerprint": remote.get("system_fingerprint"),
                          "prompt_sha256": prompt_hash, "response_sha256": hashlib.sha256(content.encode()).hexdigest(),
                          "input_tokens": input_count, "output_tokens": output_count,
                          "seconds": round(time.monotonic() - started, 3), "finish_reason": choice.get("finish_reason")}
                self.usage.records.append(record)
                if self.event_callback:
                    self.event_callback("LLM_RESPONSE", record)
                if choice.get("finish_reason") != "stop":
                    raise ResponseContractError("Model response did not finish normally; incomplete content rejected")
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ResponseContractError("Model returned a non-object JSON value")
                return data
            except (KeyError, TypeError, ValueError, IndexError):
                raise ResponseContractError("Provider response violates the JSON contract") from None
        raise ProviderError("Provider request did not complete")

    def _retry_pause(self):
        """Never issue a second billed request after cancellation or the deadline."""
        if self.checkpoint:
            self.checkpoint()
        delay = 1.0
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise BudgetExceeded("Run wall-clock budget exhausted during retry")
            delay = min(delay, remaining)
        time.sleep(delay)
        if self.checkpoint:
            self.checkpoint()


class OpenAIResponsesProvider:
    """Bounded Responses calls through the official OpenAI Python SDK.

    Deployment configuration owns the HTTPS endpoint and its credential. Every
    role call is stateless, explicitly disables remote response storage, and
    records only JSON content hashes and usage metadata. Provider failures keep
    their own terminal state; retries preserve the requested model and endpoint.
    """

    def __init__(self, settings: Settings, event_callback: Callable | None = None):
        self.settings = settings
        self.mode = "openai"
        self.model = settings.openai_model
        self.usage = Usage()
        self.event_callback = event_callback
        self.deadline = None
        self.checkpoint = None
        self._usage_unavailable = False
        self.base_url = settings.openai_base_url.rstrip("/")
        self.base_urls = [self.base_url]
        try:
            parsed = urlparse(self.base_url)
            port = parsed.port
        except ValueError:
            raise ProviderError("OpenAI Responses URL is invalid") from None
        if (parsed.scheme != "https" or not parsed.hostname
                or any(char.isspace() for char in self.base_url)):
            raise ProviderError("OpenAI Responses URL must use HTTPS and include a host")
        if parsed.username or parsed.password or "?" in self.base_url or "#" in self.base_url:
            raise ProviderError("OpenAI Responses URL must not contain credentials, query, or fragment")
        secret = settings.openai_api_key.get_secret_value()
        if not secret:
            raise ProviderError("OPENAI_API_KEY is missing; configure the server environment or .env")
        if secret in self.base_url:
            raise ProviderError("OpenAI Responses URL must not contain a credential")
        self._proxy_url = settings.openai_proxy_url.get_secret_value()
        self._proxy_credentials = []
        if self._proxy_url:
            try:
                proxy = urlparse(self._proxy_url)
                proxy.port
            except ValueError:
                raise ProviderError("OpenAI proxy URL is invalid") from None
            if (proxy.scheme not in {"http", "https"} or not proxy.hostname
                    or any(char.isspace() for char in self._proxy_url)):
                raise ProviderError("OpenAI proxy URL must use HTTP(S) and include a host")
            if "?" in self._proxy_url or "#" in self._proxy_url:
                raise ProviderError("OpenAI proxy URL must not contain query or fragment")
            if self._proxy_url in self.base_url:
                raise ProviderError("OpenAI Responses URL must not contain proxy configuration")
            self._proxy_credentials = [value for value in (
                proxy.username, proxy.password, unquote(proxy.username or ""), unquote(proxy.password or ""),
            ) if value]
        if not self.model.strip():
            raise ProviderError("OPENAI_MODEL is required")
        if settings.openai_reasoning_effort not in {"", "none", "minimal", "low", "medium", "high", "xhigh"}:
            raise ProviderError("OPENAI_REASONING_EFFORT is invalid")
        self.deployment = ("official_api" if parsed.hostname == "api.openai.com"
                           and port in {None, 443} else "openai_compatible_api")

    def metadata(self) -> dict:
        """Identify the selected deployment without publishing its credential."""
        return {
            "provider": self.mode, "model": self._safe_text(self.model),
            "base_url": self.base_url, "base_urls": list(self.base_urls),
            "authorization": "bearer", "deployment": self.deployment,
            "api": "responses", "sdk": "openai", "store": False,
            "stream": self.settings.openai_stream,
            "proxy_configured": bool(self._proxy_url),
            "reasoning_effort": self.settings.openai_reasoning_effort or "model_default",
        }

    def _safe_text(self, value) -> str | None:
        if value is None:
            return None
        text = str(value)
        for name in ("api_key", "local_api_key", "openai_api_key", "openai_proxy_url"):
            secret = getattr(self.settings, name).get_secret_value()
            if secret:
                text = text.replace(secret, "[REDACTED]")
        for secret in self._proxy_credentials:
            text = text.replace(secret, "[REDACTED]")
        return text[:512]

    @staticmethod
    def _token_count(value) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProviderError("Responses usage must contain nonnegative integer token counts")
        return value

    def _record_response(self, remote, role: str, prompt_hash: str, started: float,
                         requested_max_output_tokens: int) -> str:
        """Account for completed or rejected responses before parsing their JSON."""
        usage = getattr(remote, "usage", None)
        status = getattr(remote, "status", None)
        text_parts = []
        refusal = False
        invalid_output = False
        for item in getattr(remote, "output", None) or []:
            kind = getattr(item, "type", None)
            if kind == "reasoning":
                continue
            if kind != "message" or getattr(item, "role", None) != "assistant":
                invalid_output = True
                continue
            if getattr(item, "status", None) != "completed":
                invalid_output = True
            for block in getattr(item, "content", None) or []:
                block_kind = getattr(block, "type", None)
                if block_kind == "refusal":
                    refusal = True
                elif block_kind == "output_text" and isinstance(getattr(block, "text", None), str):
                    text_parts.append(block.text)
                else:
                    invalid_output = True
        content = "".join(text_parts)
        record = {
            "role": role, "requested_model": self._safe_text(self.model),
            "returned_model": self._safe_text(getattr(remote, "model", None)),
            "endpoint": self.base_url, "response_id": self._safe_text(getattr(remote, "id", None)),
            "prompt_sha256": prompt_hash,
            "response_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "seconds": round(time.monotonic() - started, 3),
            "finish_reason": self._safe_text(status), "api": "responses",
            "usage_available": False, "input_tokens": None, "output_tokens": None,
            "cached_input_tokens": None,
            "requested_max_output_tokens": requested_max_output_tokens,
            "output_limit_exceeded": None,
            "stream": self.settings.openai_stream,
        }
        usage_error = None
        try:
            if usage is None:
                raise ProviderError("Responses usage is missing; token budget cannot be verified")
            input_count = self._token_count(getattr(usage, "input_tokens", None))
            output_count = self._token_count(getattr(usage, "output_tokens", None))
            details = getattr(usage, "input_tokens_details", None)
            cached = self._token_count(getattr(details, "cached_tokens", 0))
            if cached > input_count:
                raise ProviderError("Responses cached input usage exceeds total input usage")
            self.usage.input_tokens += input_count
            self.usage.output_tokens += output_count
            self.usage.cached_input_tokens += cached
            record.update(usage_available=True, input_tokens=input_count,
                          output_tokens=output_count, cached_input_tokens=cached,
                          output_limit_exceeded=output_count > requested_max_output_tokens)
        except ProviderError as error:
            self._usage_unavailable = True
            usage_error = error
        self.usage.records.append(record)
        if self.event_callback:
            self.event_callback("LLM_RESPONSE", record)
        if usage_error:
            raise usage_error
        if refusal:
            raise ProviderError("Responses model declined the requested role output")
        if status != "completed" or getattr(remote, "error", None) is not None:
            raise ResponseContractError("Responses output is incomplete or failed; content rejected")
        if invalid_output or not content or len(content) > 120000:
            raise ResponseContractError("Responses output must contain completed assistant JSON text")
        if self.usage.input_tokens > self.settings.max_input_tokens:
            raise BudgetExceeded("Responses usage exceeded the input-token budget")
        if self.usage.output_tokens > self.settings.max_output_tokens:
            raise BudgetExceeded("Responses usage exceeded the output-token budget")
        return content

    def _consume_stream(self, stream):
        """Receive one terminal response; discard all intermediate event content."""
        terminal_types = {"response.completed", "response.incomplete", "response.failed"}
        with stream:
            iterator = iter(stream)
            while True:
                if self.checkpoint:
                    self.checkpoint()
                if self.deadline is not None and time.monotonic() >= self.deadline:
                    raise BudgetExceeded("Run wall-clock budget exhausted during Responses stream")
                try:
                    event = next(iterator)
                except StopIteration:
                    break
                except Exception as error:
                    # Once a stream has started, the upstream may already have
                    # billed tokens. Do not retry an interrupted generation.
                    self._usage_unavailable = True
                    raise ProviderError(f"Responses stream transport failure: {type(error).__name__}") from None
                event_type = getattr(event, "type", None)
                if event_type in terminal_types:
                    remote = getattr(event, "response", None)
                    if remote is None:
                        self._usage_unavailable = True
                        raise ResponseContractError("Responses terminal stream event has no response")
                    # Account for terminal usage before the post-call deadline
                    # check, including a response arriving after cancellation.
                    return remote
                if event_type == "error":
                    self._usage_unavailable = True
                    raise ProviderError("Responses stream returned an error event")
                if self.checkpoint:
                    self.checkpoint()
                if self.deadline is not None and time.monotonic() >= self.deadline:
                    raise BudgetExceeded("Run wall-clock budget exhausted during Responses stream")
        self._usage_unavailable = True
        raise ResponseContractError("Responses stream ended without a terminal response")

    def generate(self, role, system, payload, max_tokens=4096):
        """Call Responses with at most one explicit, budgeted transport retry."""
        if self.checkpoint:
            self.checkpoint()
        if self._usage_unavailable:
            raise BudgetExceeded("Previous Responses usage is unavailable; further calls are blocked")
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if len(serialized) > 120000:
            raise BudgetExceeded("Context exceeds application payload size limit")
        instructions = system + "\nReturn exactly one JSON object. Never include private reasoning, secrets or markdown fences."
        # Some Responses gateways require the JSON instruction in input itself.
        # Keep the payload intact and include the envelope in budget and hashes.
        input_text = "Task data (JSON):\n" + serialized
        typed_input = [
            {"role": "developer", "content": instructions},
            {"role": "user", "content": input_text},
        ]
        prompt_bytes = json.dumps(
            {"instructions": instructions, "input": typed_input},
            ensure_ascii=False, sort_keys=True,
        ).encode("utf-8")
        input_bound = len(prompt_bytes) + 128
        if self.usage.input_tokens + input_bound > self.settings.max_input_tokens:
            raise BudgetExceeded("Request cannot fit remaining conservative input-token budget")
        remaining = self.settings.max_output_tokens - self.usage.output_tokens
        if remaining < 256:
            raise BudgetExceeded("LLM output token budget exhausted")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
            raise ProviderError("max_tokens must be a positive integer")
        max_tokens = min(max_tokens, remaining)
        prompt_hash = hashlib.sha256(prompt_bytes).hexdigest()
        try:
            from openai import (
                APIConnectionError,
                APIError,
                APIResponseValidationError,
                APIStatusError,
                DefaultHttpxClient,
                OpenAI,
            )
        except ImportError:
            raise ProviderError("Install the project's OpenAI SDK dependency to use Responses") from None
        body = {
            "model": self.model, "instructions": instructions, "input": typed_input,
            "max_output_tokens": max_tokens, "store": False, "stream": self.settings.openai_stream,
            "text": {"format": {"type": "json_object"}},
        }
        if self.settings.openai_reasoning_effort:
            body["reasoning"] = {"effort": self.settings.openai_reasoning_effort}
        for attempt in range(2):
            if self.checkpoint:
                self.checkpoint()
            if self.usage.calls >= self.settings.max_calls:
                raise BudgetExceeded("LLM call budget exhausted")
            timeout = self.settings.request_timeout_s
            if not math.isfinite(timeout) or timeout <= 0:
                raise ProviderError("Responses request timeout must be finite and positive")
            if self.deadline is not None:
                available = self.deadline - time.monotonic()
                if available <= 0:
                    raise BudgetExceeded("Run wall-clock budget exhausted before Responses request")
                timeout = min(timeout, available)
            self.usage.calls += 1
            started = time.monotonic()
            transport_options = {"trust_env": False, "follow_redirects": False, "timeout": timeout}
            if self._proxy_url:
                transport_options["proxy"] = self._proxy_url
            try:
                # Use the SDK's transport class, which tracks its supported HTTP
                # library. Nested contexts close it even if SDK setup fails.
                with DefaultHttpxClient(**transport_options) as transport:
                    with OpenAI(api_key=self.settings.openai_api_key.get_secret_value(),
                                base_url=self.base_url, max_retries=0, timeout=timeout,
                                http_client=transport) as client:
                        remote = client.responses.create(**body, timeout=timeout)
                        if self.settings.openai_stream:
                            remote = self._consume_stream(remote)
            except APIConnectionError as error:
                if attempt == 0:
                    self._retry_pause()
                    continue
                raise ProviderError(f"Responses transport failure: {type(error).__name__}") from None
            except APIStatusError as error:
                if error.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                    self._retry_pause()
                    continue
                raise ProviderError(f"Responses provider returned HTTP {error.status_code}") from None
            except APIResponseValidationError:
                raise ResponseContractError("Responses provider violated its response contract") from None
            except APIError as error:
                raise ProviderError(f"Responses SDK failure: {type(error).__name__}") from None
            except (ValueError, TypeError):
                raise ProviderError("Responses SDK configuration or request is invalid") from None
            content = self._record_response(remote, role, prompt_hash, started, max_tokens)
            if self.checkpoint:
                self.checkpoint()
            if self.deadline is not None and time.monotonic() >= self.deadline:
                raise BudgetExceeded("Run wall-clock budget exhausted after Responses request")
            try:
                data = json.loads(content)
            except (ValueError, TypeError):
                raise ResponseContractError("Responses provider returned invalid JSON") from None
            if not isinstance(data, dict):
                raise ResponseContractError("Responses provider returned a non-object JSON value")
            return data
        raise ProviderError("Responses request did not complete")

    def _retry_pause(self):
        if self.checkpoint:
            self.checkpoint()
        delay = 1.0
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise BudgetExceeded("Run wall-clock budget exhausted during Responses retry")
            delay = min(delay, remaining)
        time.sleep(delay)
        if self.checkpoint:
            self.checkpoint()


class MockProvider:
    """Deterministic test double. Always labeled mock; never used as API fallback."""

    def __init__(self, event_callback=None):
        self.mode = "mock"
        self.model = "deterministic-mock-v1"
        self.usage = Usage()
        self.event_callback = event_callback

    def generate(self, role, system, payload, max_tokens=4096):
        from capability_factory.plugins import get_reference_code as reference_code

        self.usage.calls += 1
        if self.event_callback:
            self.event_callback("MOCK_RESPONSE", {"role": role, "model": self.model})
        if role == "interpreter":
            return {"objective": payload["description"], "constraints": ["遵守固定数据与特征协议"],
                    "assumptions": ["离线规则测试模式"], "warnings": [], "incompatible_requests": []}
        if role == "planner":
            second = "forest" if payload["task_spec"]["task_type"] == "tabular_binary_classification" else "nb"
            evidence = [card.get("capability_id", card.get("id", "")) for card in payload.get("evidence", [])][:2]
            return {"candidates": [{"candidate_id": "c1", "algorithm": "logistic", "variant": "default",
                                    "rationale": "可复现线性参考方案", "evidence_ids": evidence},
                                   {"candidate_id": "c2", "algorithm": second, "variant": "default",
                                    "rationale": "不同算法结构的对照方案", "evidence_ids": evidence}][:payload.get("count", 2)]}
        if role in {"coder", "repair_coder"}:
            plan = payload["plan"]
            return {"code": reference_code(payload["task_spec"]["task_type"], plan["algorithm"], plan.get("variant", "default")),
                    "explanation": "明确标记的离线模板输出"}
        if role == "reviewer":
            return {"error_type": payload["error"].get("type", "execution_error"),
                    "diagnosis": "候选未通过独立验证", "fix": "按照受限接口重新生成合法Pipeline", "repairable": True}
        if role == "curator":
            return {"summary": "已根据独立验证报告比较方案；本次为mock运行。", "limitations": ["未调用真实大模型"]}
        if role == "extractor":
            return {"capabilities": []}
        raise ProviderError("Unsupported mock role")
