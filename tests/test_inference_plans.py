"""Check GPU assignment safety and unsupported tensor-parallel configurations."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plan_inference", ROOT / "scripts/plan_inference.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONFIG = json.loads((ROOT / "configs/inference_profiles.json").read_text())


@pytest.mark.parametrize("profile", list(CONFIG["profiles"]))
def test_all_profiles_have_valid_static_plans(profile):
    plan = MODULE.build_plan(CONFIG, profile)
    assert plan["status"] == "static_plan_only_runtime_untested"


def test_four_gpu_profile_has_four_single_card_groups():
    plan = MODULE.build_plan(CONFIG, "four_gpu_14b", available_gpus=4)
    assert len(plan["endpoints"]) == 4
    assert [entry["environment"]["CUDA_VISIBLE_DEVICES"] for entry in plan["endpoints"]] == [
        "0",
        "1",
        "2",
        "3",
    ]


def test_gpu_overlap_rejected():
    config = copy.deepcopy(CONFIG)
    config["profiles"]["four_gpu_14b"]["groups"][1]["gpu_ids"] = [0]
    with pytest.raises(ValueError, match="overlap"):
        MODULE.build_plan(config, "four_gpu_14b")


def test_tp_three_is_rejected_for_40_attention_heads():
    config = copy.deepcopy(CONFIG)
    group = config["profiles"]["four_gpu_14b"]["groups"][0]
    group["gpu_ids"] = [0, 1, 2]
    group["tensor_parallel_size"] = 3
    config["profiles"]["four_gpu_14b"]["groups"] = [group]
    with pytest.raises(ValueError, match="divisible"):
        MODULE.build_plan(config, "four_gpu_14b")


def test_insufficient_devices_rejected():
    with pytest.raises(ValueError, match="more GPUs"):
        MODULE.build_plan(CONFIG, "four_gpu_14b", available_gpus=1)


def test_four_gpu_14b_profile_is_four_single_gpu_replicas():
    plan = MODULE.build_plan(CONFIG, "four_gpu_14b", available_gpus=4)
    assert plan["gpu_count"] == 4
    assert len(plan["endpoints"]) == 4
    assert [item["environment"]["CUDA_VISIBLE_DEVICES"] for item in plan["endpoints"]] == ["0", "1", "2", "3"]
    assert {item["model_id"] for item in plan["endpoints"]} == {"Qwen/Qwen2.5-Coder-14B-Instruct-AWQ"}
    assert all(item["argv"][item["argv"].index("--tensor-parallel-size") + 1] == "1" for item in plan["endpoints"])


def test_local_runtime_plan_is_explicitly_not_deployed():
    runtime = CONFIG["local_runtime"]
    assert runtime["default_profile"] == "four_gpu_14b"
    assert runtime["status"] == "operator_managed"
    assert runtime["weights_downloaded_by_algoforge"] is False
    assert runtime["process_started_by_algoforge"] is False
