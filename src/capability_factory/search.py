"""Finite, auditable candidate search; model prose cannot expand the search budget."""

import hashlib
import json
import math
from collections import Counter

from capability_factory.execution.compiler import compile_constructors
from capability_factory.providers import ResponseContractError

VARIANTS = {
    "logistic": ("default", "balanced", "regularized"),
    "forest": ("default", "balanced", "regularized", "shallower"),
    "extra_trees": ("default", "balanced", "regularized", "shallower"),
    "nb": ("default", "regularized"),
    "dummy": ("default",),
}


def check_variant(plan, model_metadata, parent_metadata=None) -> str | None:
    """Return an actionable error when a named variant lacks its promised change.

    Compare with the parent's *actual* classifier parameters, regardless of the
    parent's variant label. Without a parent, reference thresholds are C=1,
    alpha=0.5, min_samples_leaf=1, and shallower max_depth<=12. Omitted parent
    parameters use sklearn defaults (notably NB alpha=1 and tree max_depth=None).
    Leaf counts and leaf fractions are different units and cannot be compared
    without training-row metadata; a child must retain the parent's unit.
    NB force_alpha=False clamps alpha to 1e-10, so compare effective smoothing.
    This function never edits/clamps generated parameters or substitutes a model.
    """
    get = (
        plan.get
        if isinstance(plan, dict)
        else lambda key, default=None: getattr(plan, key, default)
    )
    algorithm, variant = get("algorithm"), get("variant", "default")
    if variant == "default":
        return None
    if variant not in VARIANTS.get(algorithm, ()):
        return f"Variant {variant!r} is unsupported for algorithm {algorithm!r}"
    if (
        not isinstance(model_metadata, dict)
        or model_metadata.get("actual_algorithm") != algorithm
        or not isinstance(model_metadata.get("classifier_parameters"), dict)
    ):
        return (
            "Variant validation requires parsed metadata matching the planned classifier algorithm"
        )
    parameters = model_metadata["classifier_parameters"]
    if parent_metadata is not None and (
        not isinstance(parent_metadata, dict)
        or parent_metadata.get("actual_algorithm") != algorithm
        or not isinstance(parent_metadata.get("classifier_parameters"), dict)
    ):
        return (
            "Parent metadata must identify the same algorithm and its actual classifier parameters"
        )
    parent = parent_metadata["classifier_parameters"] if parent_metadata is not None else None

    def positive(value):
        return type(value) in {int, float} and math.isfinite(value) and value > 0

    if variant == "balanced":
        accepted = (
            ("balanced", "balanced_subsample")
            if algorithm in {"forest", "extra_trees"}
            else ("balanced",)
        )
        if parameters.get("class_weight") not in accepted:
            return f"balanced requires class_weight in {accepted}; changing the variant label is insufficient"
        return None

    if variant == "regularized" and algorithm == "logistic":
        value = parameters.get("C", 1.0)
        baseline = parent.get("C", 1.0) if parent is not None else 1.0
        if parameters.get("penalty", "l2") in (None, "none"):
            return "regularized logistic requires an active penalty; changing C with penalty=None has no effect"
        if not positive(value) or not positive(baseline) or not value < baseline:
            return f"regularized logistic requires finite positive C strictly below parent/reference C={baseline!r}"
        return None

    if variant == "regularized" and algorithm == "nb":
        value = parameters.get("alpha", 1.0)
        baseline = parent.get("alpha", 1.0) if parent is not None else 0.5
        if (
            type(value) not in {int, float}
            or type(baseline) not in {int, float}
            or not math.isfinite(value)
            or not math.isfinite(baseline)
            or value < 0
            or baseline < 0
        ):
            return "regularized NB requires finite non-negative numeric alpha values, excluding booleans"
        effective = max(value, 1e-10) if parameters.get("force_alpha", True) is False else value
        parent_effective = (
            max(baseline, 1e-10)
            if parent is not None and parent.get("force_alpha", True) is False
            else baseline
        )
        if not effective > parent_effective:
            return f"regularized NB requires effective alpha strictly above parent/reference alpha={parent_effective!r}; force_alpha=False clips below 1e-10"
        return None

    if variant == "regularized" and algorithm in {"forest", "extra_trees"}:
        value = parameters.get("min_samples_leaf", 1)
        baseline = parent.get("min_samples_leaf", 1) if parent is not None else 1

        def leaf_unit(item):
            if type(item) is int and item >= 1:
                return "count"
            if type(item) is float and math.isfinite(item) and 0 < item <= 1:
                return "fraction"
            return None

        unit, parent_unit = leaf_unit(value), leaf_unit(baseline)
        if unit is None or parent_unit is None:
            return "regularized trees require valid min_samples_leaf counts or fractions, excluding booleans"
        if unit != parent_unit:
            return "Compare min_samples_leaf using the same unit as the parent/reference; counts and fractions are not directly comparable"
        if not value > baseline:
            return f"regularized trees require min_samples_leaf strictly above parent/reference value={baseline!r}"
        return None

    if variant == "shallower":
        value = parameters.get("max_depth")
        if type(value) is not int or value <= 0:
            return "shallower requires an explicit positive integer max_depth, excluding booleans"
        if parent is None:
            return None if value <= 12 else "Initial shallower variant requires max_depth<=12"
        baseline = parent.get("max_depth")
        if baseline is None:
            return None  # Any finite depth is shallower than an unbounded parent.
        if type(baseline) is not int or baseline <= 0:
            return "Parent max_depth must be a positive integer or None (unbounded)"
        if value >= baseline:
            return f"shallower requires max_depth strictly below actual parent max_depth={baseline}"
        return None
    return f"No executable parameter contract exists for {algorithm}/{variant}"


def expansion_options(parents, existing):
    used = {(item["plan"]["algorithm"], item["plan"]["variant"]) for item in existing}
    options = []
    for parent in parents:
        algorithm = parent["plan"]["algorithm"]
        for variant in VARIANTS[algorithm]:
            if (algorithm, variant) not in used:
                options.append(
                    {
                        "parent_id": parent["candidate_id"],
                        "algorithm": algorithm,
                        "variant": variant,
                    }
                )
    return options


def expansion_capacity(options):
    """Count feasible unique children, respecting each parent's two-child limit.

    Parents of the same algorithm share the same unused variants. Summing
    options per parent would double-count those variants and ask the planner
    for a set of children that cannot pass the uniqueness contract.
    """
    algorithms = {option["algorithm"] for option in options}
    return sum(
        min(
            len({option["variant"] for option in options if option["algorithm"] == algorithm}),
            2 * len({option["parent_id"] for option in options if option["algorithm"] == algorithm}),
        )
        for algorithm in algorithms
    )


def validate_plans(plans, count, dataset_id, evidence, existing, parents=None):
    if len(plans) != count:
        raise ResponseContractError("Planner candidate count does not match remaining budget")
    allowed = (
        {"logistic", "forest", "extra_trees", "dummy"}
        if dataset_id == "bank"
        else {"logistic", "nb", "dummy"}
    )
    ids = {item["candidate_id"] for item in existing}
    signatures = {(item["plan"]["algorithm"], item["plan"]["variant"]) for item in existing}
    evidence_ids = {item.get("capability_id", item.get("id")) for item in evidence}
    parent_map = {item["candidate_id"]: item for item in parents or []}
    children = Counter()
    for plan in plans:
        if plan.algorithm not in allowed or plan.variant not in VARIANTS[plan.algorithm]:
            raise ResponseContractError("Planner proposed an incompatible algorithm or variant")
        signature = (plan.algorithm, plan.variant)
        if plan.candidate_id in ids or signature in signatures:
            raise ResponseContractError("Planner duplicated an ID or algorithm/variant pair")
        ids.add(plan.candidate_id)
        signatures.add(signature)
        if any(item not in evidence_ids for item in plan.evidence_ids):
            raise ResponseContractError("Planner cited evidence that was not retrieved")
        if parents:
            if (
                plan.parent_id not in parent_map
                or plan.algorithm != parent_map[plan.parent_id]["plan"]["algorithm"]
            ):
                raise ResponseContractError(
                    "Beam child must preserve a surviving parent's algorithm"
                )
            children[plan.parent_id] += 1
            if children[plan.parent_id] > 2:
                raise ResponseContractError("A surviving parent may expand at most two children")
        elif plan.parent_id is not None:
            raise ResponseContractError("Initial candidates cannot invent a parent")


def constructor_fingerprint(code, task_spec):
    """Ignore comments, variable aliases and pipeline step names when deduplicating."""
    plan = compile_constructors(code, task_spec)

    def canonical(value):
        if isinstance(value, list):
            return [canonical(item) for item in value]
        if not isinstance(value, dict):
            return value
        value = {key: canonical(item) for key, item in value.items()}
        if value.get("kind") == "constructor" and value["name"] in {
            "Pipeline",
            "ColumnTransformer",
        }:
            key = "steps" if value["name"] == "Pipeline" else "transformers"
            steps = value["args"][0] if value["args"] else value["kwargs"].get(key)
            if isinstance(steps, dict) and "items" in steps:
                for step in steps["items"]:
                    if (
                        isinstance(step, dict)
                        and step.get("kind") in {"tuple", "list"}
                        and step.get("items")
                    ):
                        step["items"][0] = "<step>"
        return value

    return hashlib.sha256(json.dumps(canonical(plan), sort_keys=True).encode()).hexdigest()
