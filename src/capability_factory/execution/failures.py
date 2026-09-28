"""Explicit, reproducible generated-code failures for repair experiments."""

from .reference import reference_code


def failure_code(case: str, task_type: str = "tabular_binary_classification") -> str:
    source = reference_code(task_type)
    if case == "invalid_parameter":
        return source.replace("max_iter=1000", "max_iter=0")
    if case == "unknown_parameter":
        return source.replace("max_iter=1000", "unsupported_parameter=1000")
    if case == "syntax_error":
        return source.replace("def build_pipeline(task_spec):", "def build_pipeline(task_spec)")
    if case == "policy_violation":
        return "import os\n" + source
    if case == "unknown_category" and task_type == "tabular_binary_classification":
        return source.replace("handle_unknown='ignore'", "handle_unknown='error'")
    if case == "missing_imputer" and task_type == "tabular_binary_classification":
        return source.replace("('impute', SimpleImputer(strategy='median')),", "")
    raise ValueError(f"Unsupported failure injection {case} for {task_type}")
