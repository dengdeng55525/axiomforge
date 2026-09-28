from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr

from capability_factory.api import create_app
from capability_factory.inference import local_profile_metadata
from capability_factory.settings import Settings, load_settings

ROOT = Path(__file__).resolve().parents[1]


def test_local_profile_metadata_describes_static_four_gpu_plan():
    metadata = local_profile_metadata(Settings(root=ROOT, api_key=SecretStr("fixture")))
    assert metadata["profile"] == "four_gpu_14b"
    assert metadata["status"] == "planned_not_deployed"
    assert metadata["deployed"] is False
    assert metadata["gpu_count"] == 4
    assert metadata["endpoint_count"] == 4
    assert metadata["weights_downloaded_by_algoforge"] is False
    assert metadata["process_started_by_algoforge"] is False
    assert "14B" in metadata["model_ids"][0] or "14b" in metadata["model_ids"][0]


def test_settings_reads_local_profile_without_exporting_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_PROFILE", "four_gpu_14b")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fixture-secret")
    settings = load_settings(tmp_path)
    assert settings.local_profile == "four_gpu_14b"
    assert settings.api_key.get_secret_value() == "fixture-secret"


def test_api_exposes_sanitized_local_profile_for_visual_console(tmp_path):
    (tmp_path / "configs").symlink_to(ROOT / "configs", target_is_directory=True)
    app = create_app(Settings(root=tmp_path, api_key=SecretStr("fixture")))
    with TestClient(app) as client:
        response = client.get("/inference/profiles")
        assert response.status_code == 200
        body = response.json()
        assert body["active_local"]["profile"] == "four_gpu_14b"
        assert body["active_local"]["deployed"] is False
        assert body["local_runtime"]["status"] == "planned_not_deployed"
        assert "fixture" not in response.text
