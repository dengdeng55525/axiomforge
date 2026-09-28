"""Explicit in-process plugins registered by trusted application developers.

This module never discovers packages, imports a user-provided module name, or runs
registration from generated code. A plugin is privileged host code, not sandboxed
content. Code returned by a template still requires the independent AST validator.
"""
from __future__ import annotations

import math
import re
import threading
from collections.abc import Callable, Sequence
from numbers import Real

Metric = Callable[[Sequence[int], Sequence[float]], float]
Template = Callable[[str, str, str], str]

TASK_TYPES = frozenset({"tabular_binary_classification", "text_binary_classification"})
# These are existing CandidatePlan IDs; registration does not extend the executor allowlist.
ALGORITHMS = frozenset({"logistic", "forest", "extra_trees", "nb", "dummy"})
_LOCK = threading.RLock()
_METRICS: dict[str, Metric] = {}
_TEMPLATES: dict[tuple[str, str], Template] = {}


class PluginError(ValueError):
    """Plugin registration, output, or execution did not meet its trusted contract."""


def register_metric(name: str, function: Metric) -> None:
    """Register a trusted numeric metric; outputs use the plugin_<name> namespace.

    Registration is explicit and process-local. Reusing a name always fails, even
    when the same callable is supplied, so startup mistakes cannot replace metrics.
    """
    if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name):
        raise PluginError("Metric name must be a lowercase identifier of 1-48 characters")
    if not callable(function):
        raise PluginError("Metric implementation must be callable")
    with _LOCK:
        if name in _METRICS:
            raise PluginError(f"Metric already registered: {name}")
        _METRICS[name] = function


def evaluate_metrics(labels: Sequence[int], scores: Sequence[float]) -> dict[str, float]:
    """Evaluate a registry snapshot, rejecting errors instead of reporting fake scores.

    Each callable receives immutable tuple snapshots. Mutations to the registry
    during a call apply to the next evaluation, not this one. The trusted caller
    remains responsible for enforcing its label and probability input contract.
    """
    with _LOCK:
        snapshot = tuple(sorted(_METRICS.items()))
    label_snapshot, score_snapshot = tuple(labels), tuple(scores)
    results: dict[str, float] = {}
    for name, function in snapshot:
        try:
            result = function(label_snapshot, score_snapshot)
        except Exception as exc:
            raise PluginError(f"Metric plugin {name!r} failed ({type(exc).__name__})") from exc
        if isinstance(result, bool) or not isinstance(result, Real):
            raise PluginError(f"Metric plugin {name!r} must return one real number")
        try:
            numeric = float(result)
        except (OverflowError, TypeError, ValueError) as exc:
            raise PluginError(f"Metric plugin {name!r} returned an invalid number") from exc
        if not math.isfinite(numeric):
            raise PluginError(f"Metric plugin {name!r} returned a non-finite number")
        results[f"plugin_{name}"] = numeric
    return results


def _template_key(task_type: str, algorithm: str) -> tuple[str, str]:
    if not isinstance(task_type, str) or task_type not in TASK_TYPES:
        raise PluginError("Template task_type must be an existing canonical classification task")
    if not isinstance(algorithm, str) or algorithm not in ALGORITHMS:
        raise PluginError("Template algorithm must be an existing CandidatePlan algorithm ID")
    if task_type == "tabular_binary_classification" and algorithm == "nb":
        raise PluginError("The existing nb reference is only defined for text classification")
    return task_type, algorithm


def register_template(task_type: str, algorithm: str, function: Template) -> None:
    """Override one existing reference template with a trusted host callable.

    Registration changes reference code only; it grants no new allowed imports,
    constructors, datasets, planner algorithms, or sandbox permissions.
    """
    key = _template_key(task_type, algorithm)
    if not callable(function):
        raise PluginError("Template implementation must be callable")
    with _LOCK:
        if key in _TEMPLATES:
            raise PluginError(f"Template already registered: {task_type}/{algorithm}")
        _TEMPLATES[key] = function


def get_reference_code(task_type: str, algorithm: str, variant: str = "default") -> str:
    """Use a registered override or lazily import the standard reference builder."""
    key = _template_key(task_type, algorithm)
    if not isinstance(variant, str) or not variant.strip() or len(variant) > 100:
        raise PluginError("Template variant must contain 1-100 characters")
    with _LOCK:
        function = _TEMPLATES.get(key)
    if function is None:
        from .execution.reference import reference_code

        return reference_code(task_type, algorithm, variant)
    try:
        result = function(task_type, algorithm, variant)
    except Exception as exc:
        raise PluginError(f"Template plugin {task_type}/{algorithm} failed ({type(exc).__name__})") from exc
    if not isinstance(result, str) or not result.strip():
        raise PluginError("Template plugin must return nonempty Python source text")
    # This is intentionally not a validation stamp. All generated/returned code
    # must still pass the independent compiler before estimator construction.
    return result


def brier_loss(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Optional binary Brier loss example: mean squared probability error (lower is better)."""
    labels, scores = tuple(labels), tuple(scores)
    if not labels or len(labels) != len(scores):
        raise PluginError("Brier loss requires nonempty aligned labels and scores")
    if any(isinstance(label, bool) or not isinstance(label, Real) or label not in (0, 1)
           for label in labels):
        raise PluginError("Brier loss labels must be binary numbers 0 or 1")
    if any(isinstance(score, bool) or not isinstance(score, Real) or not math.isfinite(score)
           or not 0 <= score <= 1 for score in scores):
        raise PluginError("Brier loss scores must be finite probabilities in [0,1]")
    return math.fsum((float(score) - float(label)) ** 2 for label, score in zip(labels, scores)) / len(labels)


def register_builtin_examples() -> None:
    """Explicitly install the optional brier_loss example; duplicate calls are errors."""
    register_metric("brier_loss", brier_loss)
