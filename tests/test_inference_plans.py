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


def test_six_gpu_profile_has_three_two_card_groups():
    plan = MODULE.build_plan(CONFIG, "six_gpu", available_gpus=6)
    assert len(plan["endpoints"]) == 3
    assert [entry["environment"]["CUDA_VISIBLE_DEVICES"] for entry in plan["endpoints"]] == [
        "0,1",
        "2,3",
        "4,5",
    ]


def test_gpu_overlap_rejected():
    config = copy.deepcopy(CONFIG)
    config["profiles"]["six_gpu"]["groups"][1]["gpu_ids"] = [0, 1]
    with pytest.raises(ValueError, match="overlap"):
        MODULE.build_plan(config, "six_gpu")


def test_tp_six_is_rejected_for_40_attention_heads():
    config = copy.deepcopy(CONFIG)
    group = config["profiles"]["six_gpu"]["groups"][0]
    group["gpu_ids"] = list(range(6))
    group["tensor_parallel_size"] = 6
    config["profiles"]["six_gpu"]["groups"] = [group]
    with pytest.raises(ValueError, match="divisible"):
        MODULE.build_plan(config, "six_gpu")


def test_insufficient_devices_rejected():
    with pytest.raises(ValueError, match="more GPUs"):
        MODULE.build_plan(CONFIG, "six_gpu", available_gpus=1)
