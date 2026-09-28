"""User-visible contracts and immutable policy limits for the agent workflow."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=5, max_length=8000)
    dataset_id: Literal["bank", "sms"] = "bank"
    provider: Literal["deepseek", "mock", "local_http"] = "deepseek"
    max_candidates: int = Field(default=2, ge=1, le=6)
    max_repairs: int = Field(default=2, ge=0, le=2)
    use_graph: bool = True
    use_retrieval: bool = True
    orchestration: Literal["multi_role", "single_shot"] = "multi_role"
    search: Literal["compare", "beam"] = "compare"
    inject_failure: bool = False
    max_seconds: int = Field(default=900, ge=10, le=1800)


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu: int = Field(default=2, ge=1, le=2)
    memory_mib: int = Field(default=2048, ge=512, le=4096)
    timeout_s: int = Field(default=120, ge=5, le=120)


class TaskInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    incompatible_requests: list[str] = Field(default_factory=list)
    requested_run_seconds: int | None = Field(default=None, ge=10, le=1800)


class CandidatePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,48}$")
    algorithm: Literal["logistic", "forest", "extra_trees", "nb", "dummy"]
    variant: str = Field(default="default", max_length=100)
    rationale: str = Field(min_length=1, max_length=2000)
    evidence_ids: list[str] = Field(default_factory=list)
    parent_id: str | None = None


class PlanSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[CandidatePlan] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [item.candidate_id for item in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("Candidate IDs must be unique")
        return self


class GeneratedCode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=20, max_length=24000)
    explanation: str = Field(default="", max_length=3000)


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_type: str
    diagnosis: str = Field(max_length=2500)
    fix: str = Field(max_length=2500)
    repairable: bool = True


class Explanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(max_length=4000)
    limitations: list[str] = Field(default_factory=list)
