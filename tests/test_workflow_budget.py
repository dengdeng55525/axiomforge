from capability_factory.workflow import has_explicit_run_budget


def test_ordinary_algorithm_request_has_no_explicit_budget():
    description = "比较两个算法候选，按验证集 AP 选择方案并输出验证报告。"
    assert has_explicit_run_budget(description) is False


def test_chinese_seconds_budget_is_detected():
    assert has_explicit_run_budget("整个任务最多运行 120 秒。") is True


def test_english_minutes_budget_is_detected():
    assert has_explicit_run_budget("Finish the run within 2 minutes.") is True
