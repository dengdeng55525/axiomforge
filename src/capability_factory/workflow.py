"""Persistent bounded multi-role workflow with evidence, code repair and beam search."""

import hashlib
import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from capability_factory import prompts
from capability_factory.contracts import (
    Explanation,
    GeneratedCode,
    Limits,
    PlanSet,
    Review,
    RunRequest,
    TaskInterpretation,
)
from capability_factory.knowledge import KnowledgeStore
from capability_factory.optimization import analyze_resources
from capability_factory.providers import (
    BudgetExceeded,
    HTTPProvider,
    MockProvider,
    ProviderError,
    ResponseContractError,
)
from capability_factory.reporting import write_report
from capability_factory.search import (
    check_variant,
    constructor_fingerprint,
    expansion_capacity,
    expansion_options,
    validate_plans,
)
from capability_factory.settings import Settings


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)


class Cancelled(RuntimeError):
    pass


_EXPLICIT_BUDGET_PATTERN = re.compile(
    r"(?:"
    r"(?:运行时间|执行时间|运行预算|时间预算|超时时间|预算|时限|超时)\s*[为是:=：]?\s*"
    r"(?:(?:不超过|最多|至多|限制为|限于|小于|控制在)\s*)?"
    r"|(?:整个任务|整个流程|全流程|任务|运行|执行)\s*"
    r"(?:(?:最多|至多|必须|应|在|运行|执行|不超过|限定|限制|完成于)\s*){0,4}"
    r"|\b(?:run budget|time budget|wall[- ]clock budget|timeout)\s*(?:(?:of|is|at|to)\s*)?[:=]?\s*"
    r"|\b(?:run|task|workflow|execution)\s+(?:(?:must|should|finish|complete)\s+)*"
    r"(?:within|under|at most|up to|for)\s+"
    r")(?P<value>[0-9]{1,6}(?:\.[0-9]{1,3})?)\s*"
    r"(?P<unit>minutes?\b|mins?\b|seconds?\b|secs?\b|[ms]\b|分钟|分鐘|秒)",
    flags=re.IGNORECASE,
)


def explicit_run_budget_seconds(description: str) -> float | None:
    """Read numeric whole-run limits independently of model-generated values.

    Only supported, explicit run-budget phrases tighten the form's ceiling.
    Dataset durations and model counts are not run budgets. Ambiguous wording
    stays descriptive; users can always set max_seconds in the form/API.
    The ten-second floor matches the request contract.
    """

    limits = []
    for match in _EXPLICIT_BUDGET_PATTERN.finditer(description):
        unit = match["unit"].lower()
        multiplier = 60 if unit.startswith("m") or unit in {"分钟", "分鐘"} else 1
        limits.append(max(10, float(match["value"]) * multiplier))
    return min(limits) if limits else None


class Workflow:
    def __init__(self, settings: Settings, store: KnowledgeStore | None = None):
        self.settings = settings
        self.store = store or KnowledgeStore(settings.db_path)
        self.store.initialize()

    def run(self, request: RunRequest, run_id: str | None = None, cancel: threading.Event | None = None):
        from capability_factory.datasets import prepare_dataset
        from capability_factory.execution import analyze_code, validate_candidate
        from capability_factory.plugins import get_reference_code as reference_code

        run_id = run_id or uuid.uuid4().hex
        if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
            raise ValueError("run_id must be a UUID hex string")
        cancel = cancel or threading.Event()
        directory = self.settings.runs_dir / run_id
        directory.mkdir(parents=True, exist_ok=False)
        started = time.monotonic()
        deadline = started + request.max_seconds
        report = {
            "schema_version": "1.0", "run_id": run_id, "status": "running",
            "mode": "mock" if request.provider == "mock" else "real",
            "provider": request.provider, "description": request.description,
            "dataset_id": request.dataset_id, "created_at": now(), "request": request.model_dump(),
            "task_spec": {}, "model": "deterministic-mock-v1" if request.provider == "mock" else (self.settings.model if request.provider == "deepseek" else self.settings.local_model),
            "provenance": {"prompt_version": prompts.PROMPT_VERSION, "sealed_test_scored": False},
            "candidates": [], "selected_candidate_id": None, "events": [], "usage": {},
            "warnings": ["指标来自 validation_only，封存测试集保持未评分。", "执行器采用受限 AST 构造器和资源限制子进程；生产隔离需要强化运行时。"],
            "search_tree": [], "knowledge_writeback": {},
        }
        self.store.save_run(report)
        provider = None
        pending_experiences = []
        validated_fingerprints = {}

        def checkpoint():
            if cancel.is_set():
                raise Cancelled("Run cancelled by user")
            if time.monotonic() >= deadline:
                raise BudgetExceeded("Run wall-clock budget exhausted")

        def event(event_type, data=None):
            entry = {"sequence": len(report["events"]), "event_type": event_type, "type": event_type,
                     "created_at": now(), "data": data or {}}
            report["events"].append(entry)
            self.store.add_event(run_id, entry)
            if provider:
                report["usage"] = provider.usage.as_dict()
            self.store.save_run(report)
            write_json(directory / "progress.json", report)

        def ask(role, system, payload, schema, max_tokens=4096):
            checkpoint()
            for attempt in range(2):
                checkpoint()
                if isinstance(provider, HTTPProvider):
                    provider.settings.request_timeout_s = max(1, min(120, deadline - time.monotonic()))
                request_number = provider.usage.calls + 1
                stem = directory / "llm" / f"{request_number:02d}_{role}"
                write_json(stem.with_suffix(".request.json"), {"role": role, "prompt_version": prompts.PROMPT_VERSION,
                                                              "system": system, "payload": payload})
                try:
                    data = provider.generate(role, system, payload, max_tokens=max_tokens)
                    write_json(stem.with_suffix(".response.json"), data)
                    checkpoint()
                    return schema.model_validate(data)
                except (ValidationError, ResponseContractError) as error:
                    event("RESPONSE_SCHEMA_REJECTED", {"role": role, "error": type(error).__name__})
                    if attempt:
                        raise ResponseContractError(f"{role} violated its structured output contract twice") from None
                    payload = {**payload, "format_correction": "Return exactly the requested keys and types; previous output failed schema validation.",
                               "required_schema": schema.model_json_schema()}
            raise ProviderError("Unreachable response parser state")

        def make_plans(count, evidence, parents=None):
            payload = {"description": request.description, "task_spec": report["task_spec"], "evidence": evidence,
                       "count": count, "existing_plans": [item["plan"] for item in report["candidates"]]}
            if parents:
                payload["parent_candidates"] = [{"candidate_id": item["candidate_id"], "plan": item["plan"], "metrics": item["metrics"],
                                                  "model_metadata": item.get("model_metadata")} for item in parents]
                payload["expansion_options"] = expansion_options(parents, report["candidates"])
            for retry in range(2):
                plans = ask("planner", prompts.PLANNER, payload, PlanSet, 2200).candidates
                try:
                    validate_plans(plans, count, request.dataset_id, evidence, report["candidates"], parents)
                    return plans
                except ResponseContractError as error:
                    event("PLAN_REJECTED", {"error": str(error)})
                    if retry:
                        raise
                    payload["plan_correction"] = str(error)

        def execute_plan(plan, dataset):
            checkpoint()
            candidate = {"candidate_id": plan.candidate_id, "plan": plan.model_dump(), "status": "running",
                         "metrics": {}, "checks": [], "resources": {}, "repairs": [], "attempts": [],
                         "artifact_id": plan.candidate_id, "parent_id": plan.parent_id}
            report["candidates"].append(candidate)
            event("CANDIDATE_PLANNED", plan.model_dump())
            generation_payload = {"task_spec": report["task_spec"], "plan": plan.model_dump(),
                                  "evidence": report["evidence"],
                                  "reference": reference_code(report["task_spec"]["task_type"], plan.algorithm)}
            if plan.parent_id:
                parent = next(item for item in report["candidates"] if item["candidate_id"] == plan.parent_id)
                generation_payload["parent_code"] = (directory / parent["code_path"]).read_text(encoding="utf-8")
                generation_payload["parent_metadata"] = parent.get("model_metadata")
            code_reply = ask("coder", prompts.CODER, generation_payload, GeneratedCode, 2800)
            code = code_reply.code
            if request.inject_failure and len(report["candidates"]) == 1:
                code = code.replace("def build_pipeline(", "def broken_pipeline(", 1)
                candidate["injected_failure"] = True
                event("FAILURE_INJECTED", {"candidate_id": plan.candidate_id, "kind": "missing_interface", "injected": True})
            for attempt in range(request.max_repairs + 1):
                checkpoint()
                attempt_dir = directory / "candidates" / plan.candidate_id / f"attempt_{attempt}"
                attempt_dir.mkdir(parents=True, exist_ok=True)
                code_path = attempt_dir / "model.py"
                code_path.write_text(code, encoding="utf-8")
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                limits = Limits().model_dump()
                limits["timeout_s"] = max(1, min(limits["timeout_s"], int(deadline - time.monotonic())))
                event("VALIDATING", {"candidate_id": plan.candidate_id, "attempt": attempt, "code_sha256": code_hash})
                fingerprint = None
                try:
                    fingerprint = constructor_fingerprint(code, report["task_spec"])
                except ValueError:
                    pass  # The validator produces the full source-policy failure evidence.
                if fingerprint in validated_fingerprints:
                    outcome = {"status": "failed", "error": {"type": "duplicate_candidate", "stage": "search_policy", "repairable": True,
                               "message": "Constructor plan duplicates " + validated_fingerprints[fingerprint] + "; implement the planned parameter change"}}
                else:
                    try:
                        parsed_metadata = analyze_code(code, report["task_spec"], limits["cpu"])
                        parent_metadata = None
                        if plan.parent_id:
                            parent_metadata = next(item.get("model_metadata") for item in report["candidates"]
                                                   if item["candidate_id"] == plan.parent_id)
                        variant_error = check_variant(plan, parsed_metadata, parent_metadata)
                    except (ValueError, TypeError, KeyError) as error:
                        parsed_metadata = None
                        variant_error = f"Generated code could not be checked against its plan: {type(error).__name__}"
                    if variant_error:
                        outcome = {"status": "failed", "model_metadata": parsed_metadata,
                                   "error": {"type": "plan_consistency", "stage": "source_policy",
                                             "repairable": True, "message": variant_error},
                                   "checks": [], "resources": {}, "metrics": {}}
                    else:
                        outcome = validate_candidate(code, report["task_spec"], dataset, attempt_dir, limits,
                                                     cancel_check=cancel.is_set, expected_algorithm=plan.algorithm)
                snapshot = {"attempt": attempt, "code_sha256": code_hash, "code_path": str(code_path.relative_to(directory)),
                            "status": outcome["status"], "error": outcome.get("error"), "checks": outcome.get("checks", []),
                            "metrics": outcome.get("metrics", {}), "resources": outcome.get("resources", {}),
                            "containment": outcome.get("containment", {}), "model_metadata": outcome.get("model_metadata")}
                candidate["attempts"].append(snapshot)
                candidate.update({key: outcome.get(key, {} if key in {"metrics", "resources"} else None) for key in ["status", "checks", "metrics", "resources", "error", "quality_status", "model_metadata", "containment"]})
                candidate.update({"code_sha256": code_hash, "code_path": snapshot["code_path"], "explanation": code_reply.explanation})
                write_json(attempt_dir / "verification.json", outcome)
                event("VERIFIED", {"candidate_id": plan.candidate_id, "attempt": attempt, "status": outcome["status"],
                                   "metrics": outcome.get("metrics", {}), "error": outcome.get("error")})
                if candidate["repairs"]:
                    memory = candidate["repairs"][-1]
                    if memory.get("attempt") == attempt and memory.get("after_hash") == code_hash:
                        memory["validated"] = outcome["status"] == "passed"
                        pending_experiences.append({**memory, "candidate_id": plan.candidate_id})
                checkpoint()
                if outcome["status"] == "passed":
                    validated_fingerprints[fingerprint] = plan.candidate_id
                    break
                error = outcome.get("error") or {"type": "validation_error", "message": "Candidate failed independent checks", "repairable": True}
                if attempt >= request.max_repairs or not error.get("repairable", True):
                    pending_experiences.append({"error_type": error["type"], "diagnosis": error["message"],
                                                "fix": "No successful repair within budget", "validated": False})
                    break
                review = ask("reviewer", prompts.REVIEWER, {"task_spec": report["task_spec"], "code": code, "error": error,
                                                          "checks": outcome.get("checks", [])}, Review, 1200)
                candidate["repairs"].append({**review.model_dump(), "attempt": attempt + 1, "before_hash": code_hash})
                event("REPAIR_PLANNED", {"candidate_id": plan.candidate_id, **review.model_dump()})
                if not review.repairable:
                    pending_experiences.append({**review.model_dump(), "validated": False, "candidate_id": plan.candidate_id})
                    break
                code_reply = ask("repair_coder", prompts.CODER,
                                 {**generation_payload, "previous_code": code, "review": review.model_dump()}, GeneratedCode, 2800)
                code = code_reply.code
                candidate["repairs"][-1]["after_hash"] = hashlib.sha256(code.encode()).hexdigest()
            report["search_tree"].append({"candidate_id": plan.candidate_id, "parent_id": plan.parent_id,
                                          "status": candidate["status"], "average_precision": (candidate.get("metrics") or {}).get("average_precision"),
                                          "pruned": False})

        try:
            provider = MockProvider(event) if request.provider == "mock" else HTTPProvider(self.settings.model_copy(deep=True), request.provider, event)
            report["provider_metadata"] = (
                {"provider": "mock", "model": provider.model, "deployment": "deterministic_mock"}
                if request.provider == "mock" else provider.metadata()
            )
            if isinstance(provider, HTTPProvider):
                provider.deadline = deadline
                provider.checkpoint = checkpoint
            event("RECEIVED", {"mode": report["mode"], "model": report["model"]})
            if not self.store.list_capabilities():
                self.store.ingest_sources(self.settings.root)
            dataset = prepare_dataset(request.dataset_id, self.settings.root, directory / "dataset")
            report["task_spec"] = {"task_type": dataset["task_type"], "dataset_id": request.dataset_id,
                                   "positive_label": dataset["positive_label"], "feature_names": dataset.get("feature_names", []),
                                   "numeric_features": dataset.get("numeric_features", []), "categorical_features": dataset.get("categorical_features", []),
                                   "seed": 42, "primary_metric": "average_precision", "limits": Limits().model_dump(),
                                   "feature_policy": "precontact_conservative_v1" if request.dataset_id == "bank" else "normalized_group_split_v1"}
            report["provenance"]["dataset"] = dataset["manifest"]
            report["data_summary"] = {"train_rows": dataset["train_rows"], "validation_rows": dataset["validation_rows"]}
            if request.orchestration == "multi_role":
                interpretation = ask("interpreter", prompts.INTERPRETER,
                                     {"description": request.description, "task_spec": report["task_spec"]}, TaskInterpretation, 1300)
            else:
                interpretation = TaskInterpretation(objective=request.description,
                                                   assumptions=["单次生成消融：采用冻结任务策略与固定算法计划，未调用解释/规划角色。"])
            report["interpretation"] = interpretation.model_dump()
            declared_budget = explicit_run_budget_seconds(request.description)
            if declared_budget is not None:
                deadline = min(deadline, started + declared_budget)
                if isinstance(provider, HTTPProvider):
                    provider.deadline = deadline
                event("RUN_BUDGET_APPLIED", {
                    "source": "explicit_user_description",
                    "declared_seconds": declared_budget,
                    "effective_seconds": deadline - started,
                })
                checkpoint()
            if (interpretation.requested_run_seconds is not None
                    and interpretation.requested_run_seconds != declared_budget):
                report["warnings"].append(
                    "解释器返回的运行预算与可核验的用户预算不一致，已忽略该模型值；"
                    "实际预算以表单上限和明确的数字时限为准。"
                )
                event("INTERPRETER_BUDGET_IGNORED", {
                    "requested_run_seconds": interpretation.requested_run_seconds,
                    "declared_seconds": declared_budget,
                    "reason": "no_explicit_budget_in_user_description" if declared_budget is None else "budget_value_mismatch",
                })
            report["warnings"].extend(interpretation.warnings + interpretation.incompatible_requests)
            event("SPEC_VALIDATED", {"task_type": dataset["task_type"], "assumptions": interpretation.assumptions})
            evidence = self.store.search(request.description, dataset["task_type"], limit=6, use_graph=request.use_graph) if request.use_retrieval else []
            report["evidence"] = evidence
            event("KNOWLEDGE_RETRIEVED", {"count": len(evidence), "use_graph": request.use_graph,
                                          "capability_ids": [item.get("capability_id", item.get("id")) for item in evidence]})
            initial_count = min(2, request.max_candidates)
            if request.orchestration == "single_shot":
                from capability_factory.contracts import CandidatePlan

                initial_plans = [CandidatePlan(candidate_id="fixed_c1", algorithm="logistic", variant="default",
                                                rationale="预注册消融采用固定线性算法计划，非LLM规划。",
                                                evidence_ids=[card.get("capability_id", card.get("id")) for card in evidence][:2])]
            else:
                initial_plans = make_plans(initial_count, evidence)
            for plan in initial_plans:
                execute_plan(plan, dataset)
            remaining = request.max_candidates - len(report["candidates"])
            parents = sorted([item for item in report["candidates"] if item["status"] == "passed"],
                             key=lambda item: item["metrics"].get("average_precision", -1), reverse=True)[:2]
            if request.orchestration == "multi_role" and request.search == "beam" and remaining > 0 and parents:
                options = expansion_options(parents, report["candidates"])
                child_count = min(remaining, expansion_capacity(options))
                if request.provider == "mock":
                    from capability_factory.contracts import CandidatePlan

                    expanded = []
                    signatures = set()
                    for parent in parents:
                        for option in [option for option in options if option["parent_id"] == parent["candidate_id"]][:2]:
                            if len(expanded) >= child_count:
                                break
                            signature = (option["algorithm"], option["variant"])
                            if signature in signatures:
                                continue
                            signatures.add(signature)
                            expanded.append(CandidatePlan(candidate_id=f"b{len(expanded) + 1}", algorithm=parent["plan"]["algorithm"],
                                                          variant=option["variant"], rationale="离线Beam扩展测试",
                                                          evidence_ids=parent["plan"]["evidence_ids"], parent_id=parent["candidate_id"]))
                    validate_plans(expanded, child_count, request.dataset_id, evidence, report["candidates"], parents)
                else:
                    try:
                        expanded = make_plans(child_count, evidence, parents) if child_count else []
                    except ResponseContractError as error:
                        # Beam expansion is an optional search bonus. Keep the
                        # already verified parents when a local model emits an
                        # invalid child plan after retries.
                        expanded = []
                        warning = f"Beam 扩展已跳过，保留已验证候选：{error}"
                        report["warnings"].append(warning)
                        event("BEAM_SKIPPED", {
                            "requested_children": child_count,
                            "reason": str(error),
                        })
                event("BEAM_EXPANDED", {"beam_width": 2, "parents": [item["candidate_id"] for item in parents], "children": len(expanded)})
                for plan in expanded:
                    execute_plan(plan, dataset)
            valid = sorted([item for item in report["candidates"] if item["status"] == "passed"],
                           key=lambda item: (-(item["metrics"].get("average_precision", -1)), item["resources"].get("wall_seconds", 0)))
            if valid:
                report["selected_candidate_id"] = valid[0]["candidate_id"]
                report["quality_status"] = valid[0].get("quality_status")
                survivors = {item["candidate_id"] for item in valid[:2]}
                for node in report["search_tree"]:
                    node["pruned"] = node["candidate_id"] not in survivors
                    node["pruned_reason"] = None if not node["pruned"] else "outside_final_beam_or_failed_hard_checks"
                if request.orchestration == "multi_role":
                    explanation = ask("curator", prompts.CURATOR,
                                      {"selected_candidate_id": report["selected_candidate_id"],
                                       "candidates": [{"candidate_id": item["candidate_id"], "metrics": item["metrics"], "status": item["status"]} for item in report["candidates"]],
                                       "evidence_ids": [item.get("capability_id", item.get("id")) for item in evidence]}, Explanation, 1300)
                else:
                    explanation = Explanation(summary="按固定AP排序规则选择已通过验证的候选；未调用总结角色。",
                                              limitations=["single_shot消融，非完整多角色编排"])
                report["explanation"] = explanation.model_dump()
                event("COMPARED", {"selected_candidate_id": report["selected_candidate_id"]})
                checkpoint()
                report["status"] = "passed"
            else:
                report["status"] = "failed"
                report["failure_reason"] = "No candidate passed independent validation within budget"
        except Cancelled as error:
            report["status"] = "cancelled"
            report["failure_reason"] = str(error)
        except Exception as error:
            report["status"] = "failed"
            message = str(error)
            secret = self.settings.api_key.get_secret_value()
            if secret:
                message = message.replace(secret, "[REDACTED]")
            report["failure_reason"] = f"{type(error).__name__}: {message[:2000]}"
        finally:
            for item in report["candidates"]:
                if item["status"] == "running":
                    item["status"] = "cancelled" if report["status"] == "cancelled" else "failed"
            report["optimization"] = analyze_resources(report)
            report["usage"] = provider.usage.as_dict() if provider else {}
            report["finished_at"] = now()
            report["timing"] = {"wall_seconds": round(time.monotonic() - started, 3), "budget_seconds": deadline - started,
                                "request_ceiling_seconds": request.max_seconds}
            terminal_status = report["status"]
            report["status"] = "finalizing"
            report["report_paths"] = {}
            try:
                self.store.save_run(report)
                memories = []
                for experience in pending_experiences:
                    memories.append(self.store.record_experience(run_id, experience["error_type"], experience["diagnosis"],
                                                                experience["fix"], report["task_spec"].get("task_type", "unknown"), experience["validated"]))
                report["knowledge_writeback"] = {"run_saved": True, "experiences": memories}
                event("RECORDED", {"intended_status": terminal_status, "experiences": len(memories)})
                report["status"] = terminal_status
                report["report_paths"] = write_report(report, directory)
                self.store.save_run(report)
                write_json(directory / "progress.json", report)
            except Exception as error:
                report["status"] = "failed"
                report["failure_reason"] = f"Finalization failed: {type(error).__name__}"
                self.store.save_run(report)
                write_json(directory / "progress.json", report)
                write_json(directory / "report.json", report)
        return report
