"""Search budgets and genuinely distinct generated constructor plans."""

import pytest

from capability_factory.contracts import CandidatePlan
from capability_factory.execution import reference_code
from capability_factory.providers import ResponseContractError
from capability_factory.search import constructor_fingerprint, expansion_options, validate_plans


def plan(name, algorithm="logistic", variant="default", parent=None):
    return CandidatePlan(candidate_id=name, algorithm=algorithm, variant=variant,
                         rationale="fixture", parent_id=parent)


def test_duplicate_algorithm_variant_rejected_even_with_distinct_ids():
    with pytest.raises(ResponseContractError, match="duplicated"):
        validate_plans([plan("a"), plan("b")], 2, "bank", [], [])


def test_invalid_nb_variant_and_fake_evidence_rejected():
    with pytest.raises(ResponseContractError, match="incompatible"):
        validate_plans([plan("a", "nb", "balanced")], 1, "sms", [], [])
    proposed = plan("b")
    proposed.evidence_ids = ["invented"]
    with pytest.raises(ResponseContractError, match="evidence"):
        validate_plans([proposed], 1, "bank", [], [])


def test_beam_limits_two_children_and_preserves_parent_algorithm():
    parent = {"candidate_id": "p", "plan": plan("p", "forest").model_dump()}
    children = [plan("a", "forest", "balanced", "p"), plan("b", "forest", "regularized", "p"),
                plan("c", "forest", "shallower", "p")]
    with pytest.raises(ResponseContractError, match="two children"):
        validate_plans(children, 3, "bank", [], [parent], [parent])
    with pytest.raises(ResponseContractError, match="parent"):
        validate_plans([plan("x", "logistic", "balanced", "p")], 1, "bank", [], [parent], [parent])
    assert len(expansion_options([parent], [parent])) == 3


def test_constructor_fingerprint_ignores_comments_and_step_names():
    spec = {"task_type": "text_binary_classification", "seed": 42}
    source = reference_code(spec["task_type"], "logistic")
    renamed = source.replace("'tfidf'", "'different_name'").replace('"tfidf"', '"different_name"') + "\n# irrelevant comment\n"
    assert constructor_fingerprint(source, spec) == constructor_fingerprint(renamed, spec)
    changed = reference_code(spec["task_type"], "logistic", "regularized")
    assert constructor_fingerprint(source, spec) != constructor_fingerprint(changed, spec)
