"""Run limits must come from explicit user settings, never model guesses."""

import pytest

from capability_factory.workflow import explicit_run_budget_seconds


@pytest.mark.parametrize(
    "description",
    [
        "比较两个算法候选，按验证集 AP 选择方案并输出验证报告。",
        "Compare 2 models and return a report.",
        "排除 duration，通话时长为 10 秒。",
        "Predict calls lasting within 2 minutes.",
        "模型每次预测耗时 10 ms，生成验证报告。",
        "预算有限，请使用 logistic 和 forest。",
        "任务预算未指定，比较 2 models。",
    ],
)
def test_non_budget_numbers_do_not_tighten_deadline(description):
    assert explicit_run_budget_seconds(description) is None


@pytest.mark.parametrize(
    "description,seconds",
    [
        ("整个任务最多运行 120 秒。", 120),
        ("Finish the run within 2 minutes.", 120),
        ("运行时间不超过 1.5 分钟。", 90),
        ("全流程在 60 秒内完成。", 60),
        ("Run budget: 2 min", 120),
        ("timeout=30s", 30),
        ("任务最多运行 5 秒", 10),
        ("预算 120 秒，运行时间限制为 60 秒", 60),
    ],
)
def test_explicit_numeric_limit_is_normalized(description, seconds):
    assert explicit_run_budget_seconds(description) == seconds
