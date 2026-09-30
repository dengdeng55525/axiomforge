"""Load provider settings without exporting credentials to child workers."""

import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel, Field, SecretStr


class Settings(BaseModel):
    root: Path
    api_key: SecretStr = Field(default=SecretStr(""), repr=False)
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-flash"
    openai_api_key: SecretStr = Field(default=SecretStr(""), repr=False)
    openai_proxy_url: SecretStr = Field(default=SecretStr(""), repr=False)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.5"
    openai_stream: bool = True
    # Disable reasoning for bounded JSON role calls by default. Set an empty
    # value to use the configured model's default reasoning behavior.
    openai_reasoning_effort: str = "none"
    local_base_url: str = "http://127.0.0.1:8100/v1"
    # Optional comma-separated pool of OpenAI-compatible local endpoints.  A
    # single endpoint remains the default for backwards compatibility; when
    # four 4090D replicas are running set LOCAL_LLM_BASE_URLS to all four
    # URLs and the provider will spread requests across them.
    local_base_urls: str = ""
    local_api_key: SecretStr = Field(default=SecretStr(""), repr=False)
    local_model: str = "coder14"
    # Static deployment plan selected for an independently managed local server.
    # This setting never downloads weights or starts a process.
    local_profile: str = "four_gpu_14b"
    request_timeout_s: float = 120.0
    max_calls: int = 24
    max_input_tokens: int = 200000
    max_output_tokens: int = 40000

    @property
    def db_path(self) -> Path:
        return self.root / "artifacts" / "knowledge.sqlite3"

    @property
    def runs_dir(self) -> Path:
        return self.root / "artifacts" / "runs"

    @property
    def local_endpoints(self) -> list[str]:
        """Return the configured local endpoint pool in deterministic order."""

        values = [item.strip().rstrip("/") for item in self.local_base_urls.split(",") if item.strip()]
        if not values:
            base = self.local_base_url.rstrip("/")
            # The four-card profile is four independent 14B replicas.  Make
            # that pool usable out of the box while retaining a custom
            # single-endpoint URL for development and one-card machines.
            if self.local_profile == "four_gpu_14b" and base.endswith(":8100/v1"):
                host_prefix = base[: -len(":8100/v1")]
                values = [host_prefix + f":{port}/v1" for port in range(8100, 8104)]
            else:
                values = [base]
        # Keep the first occurrence only; duplicate replicas would skew the
        # round-robin scheduler and usually indicate a typo in .env.
        return list(dict.fromkeys(values))


def load_settings(root: Path | str | None = None) -> Settings:
    project = Path(root or os.environ.get("ALGOFORGE_ROOT") or Path(__file__).resolve().parents[2]).resolve()
    file_values = dotenv_values(project / ".env")

    def value(name, default):
        return os.environ.get(name, file_values.get(name) or default)

    return Settings(
        root=project,
        api_key=SecretStr(value("DEEPSEEK_API_KEY", "")),
        base_url=value("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=value("DEEPSEEK_MODEL", "deepseek-flash"),
        openai_api_key=SecretStr(value("OPENAI_API_KEY", "")),
        openai_proxy_url=SecretStr(value("OPENAI_PROXY_URL", "")),
        openai_base_url=value("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=value("OPENAI_MODEL", "gpt-5.5"),
        openai_stream=value("OPENAI_STREAM", True),
        openai_reasoning_effort=os.environ.get(
            "OPENAI_REASONING_EFFORT", file_values.get("OPENAI_REASONING_EFFORT", "none") or "",
        ),
        local_base_url=value("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8100/v1"),
        local_base_urls=value("LOCAL_LLM_ENDPOINTS", value("LOCAL_LLM_BASE_URLS", "")),
        local_api_key=SecretStr(value("LOCAL_LLM_API_KEY", "")),
        local_model=value("LOCAL_LLM_MODEL", "coder14"),
        local_profile=value("LOCAL_LLM_PROFILE", "four_gpu_14b"),
    )
