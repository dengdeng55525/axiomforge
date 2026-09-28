"""Parse generated Python as a small estimator-construction language.

This module NEVER evaluates or executes Python source. It converts an explicitly
allowed AST into a JSON-compatible constructor plan. The trusted worker converts
that plan into known sklearn objects. This is not a general Python sandbox.
"""

from __future__ import annotations

import ast
import copy
import math

REGISTRY = {
    "Pipeline": "sklearn.pipeline",
    "ColumnTransformer": "sklearn.compose",
    "SimpleImputer": "sklearn.impute",
    "StandardScaler": "sklearn.preprocessing",
    "MinMaxScaler": "sklearn.preprocessing",
    "MaxAbsScaler": "sklearn.preprocessing",
    "OneHotEncoder": "sklearn.preprocessing",
    "TfidfVectorizer": "sklearn.feature_extraction.text",
    "CountVectorizer": "sklearn.feature_extraction.text",
    "LogisticRegression": "sklearn.linear_model",
    "RandomForestClassifier": "sklearn.ensemble",
    "ExtraTreesClassifier": "sklearn.ensemble",
    "DecisionTreeClassifier": "sklearn.tree",
    "ComplementNB": "sklearn.naive_bayes",
    "MultinomialNB": "sklearn.naive_bayes",
    "BernoulliNB": "sklearn.naive_bayes",
    "DummyClassifier": "sklearn.dummy",
}
SPEC_FIELDS = {
    "task_type",
    "feature_names",
    "numeric_features",
    "categorical_features",
    "positive_label",
    "seed",
}


class CodePolicyError(ValueError):
    """A generated program uses syntax outside the constructor policy."""


def compile_constructors(code: str, task_spec: dict, cpu_limit: int = 2) -> dict:
    if not isinstance(code, str) or not code.strip() or len(code.encode()) > 60000:
        raise CodePolicyError("Generated source must be non-empty and at most 60,000 bytes")
    try:
        tree = ast.parse(code, mode="exec")
    except (SyntaxError, RecursionError) as error:
        raise CodePolicyError(f"Invalid Python syntax: {error}") from error
    if sum(1 for _ in ast.walk(tree)) > 2000:
        raise CodePolicyError("Generated source exceeds 2,000 AST nodes")
    imported: set[str] = set()
    function = None
    for node in tree.body:
        if _is_docstring(node):
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level or node.module not in set(REGISTRY.values()):
                raise CodePolicyError("Only explicitly listed sklearn imports are allowed")
            for item in node.names:
                if item.asname or REGISTRY.get(item.name) != node.module:
                    raise CodePolicyError(f"Disallowed import or alias: {item.name}")
                imported.add(item.name)
        elif isinstance(node, ast.FunctionDef) and function is None:
            function = node
        else:
            raise CodePolicyError("Top level may contain approved imports and one function only")
    if function is None or function.name != "build_pipeline":
        raise CodePolicyError("Define exactly one function named build_pipeline(task_spec)")
    args = function.args
    if (
        function.decorator_list
        or function.returns
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or args.defaults
        or len(args.args) != 1
        or args.args[0].arg != "task_spec"
        or args.args[0].annotation
    ):
        raise CodePolicyError("Function signature must be exactly build_pipeline(task_spec)")
    local: dict[str, object] = {}
    local_sizes: dict[str, int] = {}
    expansion_budget = 0
    result = None

    def expression(node, depth=0):
        nonlocal expansion_budget
        expansion_budget += 1
        if expansion_budget > 10000:
            raise CodePolicyError("Expanded constructor plan exceeds 10,000 nodes")
        if depth > 24:
            raise CodePolicyError("Constructor expressions exceed 24 levels")
        if isinstance(node, ast.Constant):
            if type(node.value) not in {str, int, float, bool, type(None)}:
                raise CodePolicyError(
                    "Only strings, numbers, booleans, and None literals are allowed"
                )
            if isinstance(node.value, str) and len(node.value) > 10000:
                raise CodePolicyError("String literal exceeds 10,000 characters")
            if type(node.value) in {int, float} and (
                abs(node.value) > 10**12 or not math.isfinite(node.value)
            ):
                raise CodePolicyError("Numeric literal exceeds safe construction range")
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = expression(node.operand, depth + 1)
            if type(value) not in {int, float}:
                raise CodePolicyError("Unary signs apply to numbers only")
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, (ast.List, ast.Tuple)):
            return {
                "kind": "tuple" if isinstance(node, ast.Tuple) else "list",
                "items": [expression(item, depth + 1) for item in node.elts],
            }
        if isinstance(node, ast.Dict):
            pairs = []
            for key, value in zip(node.keys, node.values):
                if key is None:
                    raise CodePolicyError("Dictionary unpacking is not allowed")
                parsed_key = expression(key, depth + 1)
                if type(parsed_key) not in {str, int}:
                    raise CodePolicyError("Dictionary keys must be literal strings or integers")
                pairs.append([parsed_key, expression(value, depth + 1)])
            return {"kind": "dict", "items": pairs}
        if isinstance(node, ast.Name) and node.id in local:
            expansion_budget += local_sizes[node.id]
            if expansion_budget > 10000:
                raise CodePolicyError("Local-variable expansion exceeds 10,000 nodes")
            return copy.deepcopy(local[node.id])
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "task_spec"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in SPEC_FIELDS
        ):
            key = node.slice.value
            if key not in task_spec:
                raise CodePolicyError(f"Missing safe task field {key}")
            value = task_spec[key]
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return {"kind": "list", "items": list(value)}
            if type(value) in {str, int}:
                return value
            raise CodePolicyError(f"Unsupported safe task field type: {key}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in imported:
                raise CodePolicyError(f"Constructor is not explicitly imported/allowed: {name}")
            if any(isinstance(item, ast.Starred) for item in node.args):
                raise CodePolicyError("Argument unpacking is not allowed")
            kwargs = {}
            for keyword in node.keywords:
                if keyword.arg is None or keyword.arg in kwargs:
                    raise CodePolicyError("Keyword unpacking/duplicates are not allowed")
                kwargs[keyword.arg] = expression(keyword.value, depth + 1)
            _validate_parameters(name, kwargs, cpu_limit)
            positional = [expression(item, depth + 1) for item in node.args]
            # Positional arguments are only used for structural containers. This
            # prevents bypassing controls such as vectorizer input='filename'.
            if positional and (
                name not in {"Pipeline", "ColumnTransformer"} or len(positional) != 1
            ):
                raise CodePolicyError(
                    "Only Pipeline/ColumnTransformer accept one positional argument"
                )
            return {"kind": "constructor", "name": name, "args": positional, "kwargs": kwargs}
        raise CodePolicyError(f"Disallowed expression: {type(node).__name__}")

    for node in function.body:
        if _is_docstring(node):
            continue
        if result is not None:
            raise CodePolicyError("Statements after return are not allowed")
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (
                not isinstance(target, ast.Name)
                or target.id.startswith("_")
                or target.id in imported
                or target.id == "task_spec"
            ):
                raise CodePolicyError("Assignments must use ordinary non-reserved local names")
            local[target.id] = expression(node.value)
            local_sizes[target.id] = _plan_size(local[target.id])
        elif isinstance(node, ast.Return) and node.value is not None:
            result = expression(node.value)
        else:
            raise CodePolicyError(f"Disallowed statement: {type(node).__name__}")
    if not isinstance(result, dict) or result.get("kind") != "constructor":
        raise CodePolicyError("build_pipeline must return an approved constructor object")
    if result.get("name") != "Pipeline":
        raise CodePolicyError("The top-level estimator must be a Pipeline")
    return result


def _plan_size(value: object) -> int:
    if isinstance(value, dict):
        return 1 + sum(_plan_size(item) for item in value.values())
    if isinstance(value, list):
        return 1 + sum(_plan_size(item) for item in value)
    return 1


def _is_docstring(node) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _validate_parameters(name: str, kwargs: dict, cpu_limit: int) -> None:
    if kwargs.get("memory") is not None:
        raise CodePolicyError("Pipeline disk caching is disabled")
    if "input" in kwargs and kwargs["input"] != "content":
        raise CodePolicyError("Text input must be content; filenames/files are forbidden")
    for parameter in ("preprocessor", "tokenizer"):
        if kwargs.get(parameter) is not None:
            raise CodePolicyError(f"Custom {parameter} is disabled")
    if "analyzer" in kwargs and kwargs["analyzer"] not in ("word", "char", "char_wb"):
        raise CodePolicyError("Only built-in text analyzers are allowed")
    if kwargs.get("n_jobs") is not None:
        jobs = kwargs["n_jobs"]
        if type(jobs) is not int or not 1 <= jobs <= cpu_limit:
            raise CodePolicyError(f"n_jobs must be between 1 and {cpu_limit}")
    bounds = {
        "n_estimators": (1, 1000),
        "max_iter": (1, 10000),
        "max_depth": (1, 64),
        "max_features": (1, 100000),
    }
    for parameter, (low, high) in bounds.items():
        value = kwargs.get(parameter)
        if type(value) is int and not low <= value <= high:
            raise CodePolicyError(f"{name}.{parameter} exceeds safe range {low}..{high}")
    if "verbose" in kwargs and kwargs["verbose"] not in (0, False):
        raise CodePolicyError("Verbose estimator logging is disabled")
    if name in {"RandomForestClassifier", "ExtraTreesClassifier", "DecisionTreeClassifier"}:
        if kwargs.get("warm_start"):
            raise CodePolicyError("warm_start is disabled for reproducible independent candidates")
    stochastic = name in {
        "RandomForestClassifier",
        "ExtraTreesClassifier",
        "DecisionTreeClassifier",
    }
    stochastic = stochastic or (
        name == "DummyClassifier" and kwargs.get("strategy") in ("stratified", "uniform")
    )
    stochastic = stochastic or (
        name == "LogisticRegression" and kwargs.get("solver") in ("sag", "saga", "liblinear")
    )
    if stochastic and (
        type(kwargs.get("random_state")) is not int or not 0 <= kwargs["random_state"] <= 2**32 - 1
    ):
        raise CodePolicyError(
            f"{name} requires an explicit integer random_state for reproducibility"
        )


def inspect_constructor_plan(plan: dict) -> dict:
    """Identify the actual final classifier without importing/executing it.

    Metadata is derived from the compiler output, never from model prose or the
    planner's claimed algorithm. Nested final Pipelines are followed explicitly.
    """
    constructors = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("kind") == "constructor":
                constructors.append(value["name"])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(plan)
    current = plan
    classifier_path = []
    for _ in range(32):
        if current.get("kind") != "constructor":
            raise CodePolicyError("Final pipeline step must be an approved classifier constructor")
        if current["name"] != "Pipeline":
            break
        args, kwargs = current["args"], current["kwargs"]
        if args and "steps" in kwargs:
            raise CodePolicyError("Pipeline steps cannot be provided twice")
        steps = args[0] if args else kwargs.get("steps")
        if not isinstance(steps, dict) or steps.get("kind") not in {"list", "tuple"}:
            raise CodePolicyError("Pipeline steps must be a non-empty literal sequence")
        if not steps["items"]:
            raise CodePolicyError("Pipeline must have at least one classifier step")
        final_step = steps["items"][-1]
        if (
            not isinstance(final_step, dict)
            or final_step.get("kind") not in {"list", "tuple"}
            or len(final_step["items"]) != 2
            or not isinstance(final_step["items"][0], str)
        ):
            raise CodePolicyError("Final pipeline step must be a (name, estimator) pair")
        name, estimator = final_step["items"]
        classifier_path.append(name)
        if not isinstance(estimator, dict):
            raise CodePolicyError("Final pipeline step cannot be passthrough/None or a literal")
        current = estimator
    else:
        raise CodePolicyError("Nested final pipelines exceed inspection depth")
    classifier = current["name"]
    algorithms = {
        "LogisticRegression": "logistic",
        "RandomForestClassifier": "forest",
        "ExtraTreesClassifier": "extra_trees",
        "DecisionTreeClassifier": "decision_tree",
        "ComplementNB": "nb",
        "MultinomialNB": "nb",
        "BernoulliNB": "nb",
        "DummyClassifier": "dummy",
    }
    if classifier not in algorithms:
        raise CodePolicyError(f"Final estimator is not an approved classifier: {classifier}")
    return {
        "actual_algorithm": algorithms[classifier],
        "classifier_class": classifier,
        "classifier_path": classifier_path,
        "classifier_parameters": {
            key: _literal_metadata(value) for key, value in current["kwargs"].items()
        },
        "constructor_classes": constructors,
        "constructor_count": len(constructors),
        "source": "independently_parsed_constructor_plan",
    }


def _literal_metadata(value):
    if isinstance(value, list):
        return [_literal_metadata(item) for item in value]
    if not isinstance(value, dict):
        return value
    kind = value.get("kind")
    if kind in {"list", "tuple"}:
        return [_literal_metadata(item) for item in value["items"]]
    if kind == "dict":
        return {str(key): _literal_metadata(item) for key, item in value["items"]}
    if kind == "constructor":
        return {"constructor": value["name"]}
    return {key: _literal_metadata(item) for key, item in value.items()}


def analyze_code(code: str, task_spec: dict, cpu_limit: int = 2) -> dict:
    """Convenient metadata-only public API; no estimator is instantiated."""
    return inspect_constructor_plan(compile_constructors(code, task_spec, cpu_limit))


def instantiate_plan(plan: object) -> object:
    """Worker-only constructor interpreter; never accepts a source string."""
    import importlib

    if not isinstance(plan, dict):
        if type(plan) in {str, int, float, bool, type(None)}:
            return plan
        raise CodePolicyError("Unexpected constructor-plan value")
    kind = plan.get("kind")
    if kind in {"list", "tuple"}:
        values = [instantiate_plan(item) for item in plan["items"]]
        return tuple(values) if kind == "tuple" else values
    if kind == "dict":
        return {key: instantiate_plan(value) for key, value in plan["items"]}
    if kind == "constructor" and plan.get("name") in REGISTRY:
        name = plan["name"]
        constructor = getattr(importlib.import_module(REGISTRY[name]), name)
        return constructor(
            *[instantiate_plan(item) for item in plan["args"]],
            **{key: instantiate_plan(value) for key, value in plan["kwargs"].items()},
        )
    raise CodePolicyError("Unknown constructor-plan operation")
