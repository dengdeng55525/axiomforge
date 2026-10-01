from fastapi.testclient import TestClient

from capability_factory.api import create_app
from capability_factory.gpu_status import probe_gpus
from capability_factory.settings import Settings


def test_probe_gpus_returns_four_cpu_safe_slots_when_nvidia_smi_is_missing(monkeypatch):
    monkeypatch.setattr("capability_factory.gpu_status.shutil.which", lambda _: None)

    result = probe_gpus()

    assert result["schema_version"] == "gpu-status.v1"
    assert result["status"] == "unavailable"
    assert result["enabled_count"] == 0
    assert len(result["devices"]) == 4
    assert all(device["state"] == "unavailable" for device in result["devices"])


def test_probe_gpus_parses_visible_cards_and_keeps_missing_slots(monkeypatch):
    class Completed:
        returncode = 0
        stdout = """0, NVIDIA RTX 4090D, 12, 1024, 24564, 44
2, NVIDIA RTX 4090D, 0, 2048, 24564, 39
"""

    monkeypatch.setattr("capability_factory.gpu_status.shutil.which", lambda _: "/usr/bin/nvidia-smi")
    monkeypatch.setattr("capability_factory.gpu_status.subprocess.run", lambda *args, **kwargs: Completed())

    result = probe_gpus()

    assert result["status"] == "partial"
    assert result["visible_count"] == result["enabled_count"] == 2
    assert result["devices"][0]["enabled"] is True
    assert result["devices"][0]["utilization_percent"] == 12
    assert result["devices"][1]["enabled"] is False
    assert result["devices"][2]["memory_used_mib"] == 2048


def test_gpu_status_api_is_read_only_and_survives_cpu_host(tmp_path, monkeypatch):
    monkeypatch.setattr("capability_factory.gpu_status.shutil.which", lambda _: None)
    app = create_app(Settings(root=tmp_path))

    with TestClient(app) as client:
        health = client.get("/health")
        direct = client.get("/system/gpus")

    assert health.status_code == direct.status_code == 200
    assert health.json()["gpu_status"] == direct.json()
    assert direct.json()["expected_count"] == 4
    assert direct.json()["enabled_count"] == 0
