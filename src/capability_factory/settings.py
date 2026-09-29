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
    local_base_url: str = "http://127.0.0.1:8100/v1"
    local_model: str = "coder_a"
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
        local_base_url=value("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8100/v1"),
        local_model=value("LOCAL_LLM_MODEL", "coder_a"),
        local_profile=value("LOCAL_LLM_PROFILE", "four_gpu_14b"),
    )
