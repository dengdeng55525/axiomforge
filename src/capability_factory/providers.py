"""Budgeted HTTP inference, explicit mock mode, no silent provider fallback."""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urlparse

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
        self.base_url = (settings.base_url if mode == "deepseek" else settings.local_base_url).rstrip("/")
        parsed = urlparse(self.base_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ProviderError("Provider URL must not contain credentials, query, or fragment")
        if mode == "deepseek" and (parsed.scheme != "https" or parsed.hostname != "api.deepseek.com"):
            raise ProviderError("DeepSeek credentials can only be sent to the official HTTPS host")
        if mode == "deepseek" and not settings.api_key.get_secret_value():
            raise ProviderError("DEEPSEEK_API_KEY is missing; configure a private .env or environment")

    def metadata(self) -> dict:
        """Return UI-safe connection metadata without credentials or prompts."""

        return {
            "provider": self.mode,
            "model": self.model,
            "base_url": self.base_url,
            "authorization": "bearer" if self.mode == "deepseek" else "none",
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
            try:
                response = httpx.post(self.base_url + "/chat/completions", headers=headers, json=body,
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
