"""Static metadata for independently deployed local inference servers.

AlgoForge consumes an OpenAI-compatible HTTP endpoint when ``local_http`` is
selected.  This module only reads the checked-in deployment plan; it never
downloads model weights, probes a GPU, or starts a serving process.
"""

import json
from pathlib import Path


def load_inference_profiles(root: Path | str) -> dict:
    """Load the repository's static, pinned inference configuration."""

    path = Path(root) / "configs" / "inference_profiles.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"profiles": {}, "models": {}, "local_runtime": {}, "config_error": "unreadable"}
    if not isinstance(value, dict):
        return {"profiles": {}, "models": {}, "local_runtime": {}, "config_error": "invalid_root"}
    return value


def local_profile_metadata(settings) -> dict:
    """Return safe profile metadata suitable for ``/health`` and UI cards."""

    config = load_inference_profiles(settings.root)
    profile_name = settings.local_profile
    profile = config.get("profiles", {}).get(profile_name)
    runtime = config.get("local_runtime", {})
    if not isinstance(profile, dict):
        return {
            "profile": profile_name,
            "status": "configuration_error",
            "configured": bool(settings.local_base_url),
            "base_url": settings.local_base_url,
            "model": settings.local_model,
            "error": "selected profile is absent from configs/inference_profiles.json",
        }

    model_ids = []
    for group in profile.get("groups", []):
        model_key = group.get("model")
        model = config.get("models", {}).get(model_key, {})
        model_id = model.get("model_id")
        if model_id and model_id not in model_ids:
            model_ids.append(model_id)
    return {
        "profile": profile_name,
        "status": runtime.get("status", "planned_not_deployed"),
        "configured": bool(settings.local_base_url),
        "deployed": False,
        "base_url": settings.local_base_url,
        "served_model": settings.local_model,
        "model_ids": model_ids,
        "gpu_count": profile.get("gpu_count"),
        "recommended_host_ram_gib": profile.get("recommended_host_ram_gib"),
        "endpoint_count": len(profile.get("groups", [])),
        "serving_stack": runtime.get("serving_stack", "vllm_openai_compatible"),
        "transport": runtime.get("transport", "openai_compatible_http"),
        "weights_downloaded_by_algoforge": bool(runtime.get("weights_downloaded_by_algoforge", False)),
        "process_started_by_algoforge": bool(runtime.get("process_started_by_algoforge", False)),
        "health_path": runtime.get("health_path", "/health"),
        "chat_path": runtime.get("chat_path", "/v1/chat/completions"),
    }

