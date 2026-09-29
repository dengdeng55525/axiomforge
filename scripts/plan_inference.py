"""Validate and print a deployment plan. Never launch processes or fetch weights."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_plan(config, profile_name, available_gpus=None):
    profile = config["profiles"][profile_name]
    if available_gpus is not None and available_gpus < profile["gpu_count"]:
        raise ValueError("Profile requires more GPUs than explicitly available")
    used_devices, used_ports, used_names = set(), set(), set()
    endpoints = []
    for group in profile["groups"]:
        devices = group["gpu_ids"]
        tp = group["tensor_parallel_size"]
        model = config["models"][group["model"]]
        if tp < 1 or len(devices) != tp:
            raise ValueError("GPU group size and tensor_parallel_size must agree")
        if model["attention_heads"] % tp:
            raise ValueError("Attention heads must be divisible by tensor parallel size")
        if len(devices) != len(set(devices)) or used_devices.intersection(devices):
            raise ValueError("GPU groups must not overlap")
        if any(
            not isinstance(device, int) or device < 0 or device >= profile["gpu_count"]
            for device in devices
        ):
            raise ValueError("GPU device outside declared profile range")
        if group["port"] in used_ports or group["name"] in used_names:
            raise ValueError("Endpoint ports and names must be unique")
        if not 1024 <= group["port"] <= 65535:
            raise ValueError("Endpoint port must be an unprivileged TCP port")
        revision = model["revision"]
        if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
            raise ValueError("A pinned hexadecimal model commit is required")
        used_devices.update(devices)
        used_ports.add(group["port"])
        used_names.add(group["name"])
        served_model_name = group.get("served_model_name", group["name"])
        if not isinstance(served_model_name, str) or not served_model_name.strip():
            raise ValueError("served_model_name must be a non-empty string")
        argv = [
            "vllm",
            "serve",
            model["model_id"],
            "--revision",
            revision,
            "--tokenizer-revision",
            revision,
            "--served-model-name",
            served_model_name,
            "--host",
            "127.0.0.1",
            "--port",
            str(group["port"]),
            "--tensor-parallel-size",
            str(tp),
            "--max-model-len",
            str(config["default_max_model_len"]),
            "--max-num-seqs",
            str(config["default_max_num_seqs"]),
            "--gpu-memory-utilization",
            str(config["default_gpu_memory_utilization"]),
            "--dtype",
            model["dtype"],
        ]
        if model["quantization"]:
            argv.extend(["--quantization", model["quantization"]])
        if config.get("local_runtime", {}).get("enforce_eager", False):
            argv.append("--enforce-eager")
        endpoints.append(
            {
                "name": group["name"],
                "served_model_name": served_model_name,
                "environment": {"CUDA_VISIBLE_DEVICES": ",".join(map(str, devices))},
                "argv": argv,
                "base_url": f"http://127.0.0.1:{group['port']}/v1",
                "model_id": model["model_id"],
                "model_revision": revision,
            }
        )
    if used_devices != set(range(profile["gpu_count"])):
        raise ValueError("Declared GPUs must be assigned exactly once")
    return {
        "profile": profile_name,
        "status": "static_plan_only_runtime_untested",
        "gpu_count": profile["gpu_count"],
        "recommended_host_ram_gib": profile["recommended_host_ram_gib"],
        "endpoints": endpoints,
        "remaining_preflight": [
            "pin serving runtime and image digest",
            "verify CUDA/driver/quantization kernel",
            "measure host RAM and topology",
            "run real GPU smoke and load tests",
        ],
        "endpoint_pool_env": "LOCAL_LLM_ENDPOINTS=" + ",".join(item["base_url"] for item in endpoints),
        "served_model_name": endpoints[0]["served_model_name"] if endpoints else None,
        "enforce_eager": bool(config.get("local_runtime", {}).get("enforce_eager", False)),
    }


def main():
    config = json.loads((ROOT / "configs/inference_profiles.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(config["profiles"]), default="single_gpu")
    parser.add_argument("--available-gpus", type=int)
    args = parser.parse_args()
    try:
        plan = build_plan(config, args.profile, args.available_gpus)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
