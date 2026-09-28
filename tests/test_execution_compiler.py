import json

import pytest

from capability_factory.execution.compiler import CodePolicyError, compile_constructors
from capability_factory.execution.failures import failure_code
from capability_factory.execution.reference import reference_code

SPEC = {
    "task_type": "tabular_binary_classification",
    "numeric_features": ["age"],
    "categorical_features": ["job"],
    "feature_names": ["age", "job"],
    "positive_label": "yes",
    "seed": 42,
}


@pytest.mark.parametrize("algorithm", ["logistic", "forest", "extra_trees", "dummy"])
def test_reference_compiles_to_json_safe_plan(algorithm):
    result = compile_constructors(reference_code(SPEC["task_type"], algorithm), SPEC)
    assert result["name"] == "Pipeline"
    assert json.loads(json.dumps(result)) == result


@pytest.mark.parametrize("algorithm", ["logistic", "nb", "dummy"])
def test_text_reference_compiles(algorithm):
    result = compile_constructors(reference_code("text_binary_classification", algorithm), SPEC)
    assert result["name"] == "Pipeline"


@pytest.mark.parametrize(
    "source",
    [
        "import os\ndef build_pipeline(task_spec):\n    return os.system('true')",
        "from os import system\ndef build_pipeline(task_spec):\n    return system('true')",
        "def build_pipeline(task_spec):\n    return __import__('os')",
        "def build_pipeline(task_spec):\n    return open('/etc/passwd')",
        "def build_pipeline(task_spec):\n    return eval('1')",
        "def build_pipeline(task_spec):\n    return task_spec.__class__",
        "def build_pipeline(task_spec):\n    return task_spec['validation_labels_path']",
        "def build_pipeline(task_spec):\n    return [x for x in range(10)]",
        "def build_pipeline(task_spec):\n    while True:\n        pass",
        "@print\ndef build_pipeline(task_spec):\n    return 1",
        "def build_pipeline(task_spec):\n    return (lambda: 1)()",
        "from sklearn.pipeline import Pipeline as Evil\ndef build_pipeline(task_spec):\n    return Evil([])",
        "from sklearn.pipeline import Pipeline\ndef build_pipeline(task_spec):\n    Pipeline = 'x'\n    return Pipeline([])",
        "from sklearn.pipeline import Pipeline\ndef build_pipeline(task_spec):\n    p = Pipeline([])\n    return p.set_params()",
        "from sklearn.pipeline import Pipeline\ndef build_pipeline(task_spec):\n    return Pipeline([], memory='/tmp/cache')",
        "from sklearn.pipeline import Pipeline\nfrom sklearn.feature_extraction.text import TfidfVectorizer\ndef build_pipeline(task_spec):\n    return Pipeline([('v', TfidfVectorizer(input='filename'))])",
        "from sklearn.pipeline import Pipeline\nfrom sklearn.feature_extraction.text import TfidfVectorizer\ndef build_pipeline(task_spec):\n    return Pipeline([('v', TfidfVectorizer('filename'))])",
        "from sklearn.pipeline import Pipeline\nfrom sklearn.ensemble import RandomForestClassifier\ndef build_pipeline(task_spec):\n    return Pipeline([('m', RandomForestClassifier(n_estimators=999999999))])",
        "from sklearn.pipeline import Pipeline\nfrom sklearn.ensemble import RandomForestClassifier\ndef build_pipeline(task_spec):\n    return Pipeline([('m', RandomForestClassifier(n_jobs=-1))])",
    ],
)
def test_rejects_escapes_and_resource_bombs(source):
    with pytest.raises(CodePolicyError):
        compile_constructors(source, SPEC)


def test_exponential_assignment_expansion_is_bounded():
    source = "from sklearn.pipeline import Pipeline\ndef build_pipeline(task_spec):\n    x = [1]\n"
    source += "    x = [x, x]\n" * 100
    source += "    return Pipeline(x)\n"
    with pytest.raises(CodePolicyError, match="expansion|Expanded"):
        compile_constructors(source, SPEC)


def test_failure_injection_and_unknown_variant_are_explicit():
    for case in ("syntax_error", "policy_violation", "invalid_parameter"):
        with pytest.raises(CodePolicyError):
            compile_constructors(failure_code(case), SPEC)
    with pytest.raises(ValueError, match="Unknown reference variant"):
        reference_code(SPEC["task_type"], variant="mystery")
