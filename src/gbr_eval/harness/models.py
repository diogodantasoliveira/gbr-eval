"""Core data models for the eval harness."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Layer(StrEnum):
    ENGINEERING = "engineering"
    PRODUCT = "product"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"


class Tier(StrEnum):
    GATE = "gate"
    REGRESSION = "regression"
    CANARY = "canary"


class Category(StrEnum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    DECISION = "decision"
    CITATION = "citation"
    COST = "cost"
    LATENCY = "latency"
    CODE_QUALITY = "code_quality"
    TENANT_ISOLATION = "tenant_isolation"
    CONVENTION = "convention"


class EvaluationMode(StrEnum):
    PER_FILE = "per_file"
    HOLISTIC = "holistic"


class ScoringMode(StrEnum):
    WEIGHTED = "weighted"
    BINARY = "binary"
    HYBRID = "hybrid"


class ScoreReducer(StrEnum):
    MEAN = "mean"
    AT_LEAST_ONE = "at_least_one"
    ALL_PASS = "all_pass"
    MAJORITY = "majority"
    MEDIAN = "median"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GraderKind(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM_TRIAGE = "llm_triage"
    LLM_DEEP = "llm_deep"


class GraderStatus(StrEnum):
    GRADED = "graded"
    ERROR = "error"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "n/a"


class GateResult(StrEnum):
    GO = "go"
    CONDITIONAL_GO = "conditional_go"
    NO_GO = "no_go"
    NO_GO_ABSOLUTE = "no_go_absolute"


class GraderSpec(BaseModel):
    type: str
    kind: GraderKind = GraderKind.DETERMINISTIC
    field: str | None = None
    weight: float = 1.0
    required: bool = False
    config: dict[str, Any] = Field(default_factory=dict)
    model_role: str | None = None


class GraderContext(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    previous_results: list[GraderResult] = Field(default_factory=list)


class TaskInput(BaseModel):
    endpoint: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    fixture_path: str | None = None


class Task(BaseModel):
    task_id: str
    category: Category
    component: str
    layer: Layer
    tier: Tier = Tier.GATE
    tenant_profile: str = "global"
    description: str = ""
    input: TaskInput
    expected: dict[str, Any] = Field(default_factory=dict)
    graders: list[GraderSpec]
    scoring_mode: ScoringMode = ScoringMode.WEIGHTED
    pass_threshold: float = Field(ge=0.0, le=1.0, default=0.95)
    target_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    baseline_run_id: str | None = None
    regression_signal: str | None = None
    eval_owner: str | None = None
    eval_cadence: str | None = None
    golden_set_tags: list[str] | None = None
    epochs: int = Field(default=1, ge=1, le=100)
    reducers: list[ScoreReducer] = Field(default_factory=lambda: [ScoreReducer.MEAN])
    evaluation_mode: EvaluationMode = EvaluationMode.PER_FILE
    primary_reducer: ScoreReducer = ScoreReducer.MEAN

    @model_validator(mode="after")
    def _validate_thresholds(self) -> Task:
        if self.target_threshold is not None and self.target_threshold < self.pass_threshold:
            raise ValueError(
                f"target_threshold ({self.target_threshold}) must be >= pass_threshold ({self.pass_threshold})"
            )
        if self.primary_reducer not in self.reducers:
            raise ValueError(
                f"primary_reducer ({self.primary_reducer}) must be in reducers list ({self.reducers})"
            )
        return self


class GraderResult(BaseModel):
    grader_type: str
    field: str | None = None
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    weight: float = 1.0
    required: bool = False
    details: str = ""
    error: str | None = None
    severity: Severity | None = None
    file_path: str | None = None
    status: GraderStatus = GraderStatus.GRADED


class TaskResult(BaseModel):
    task_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    grader_results: list[GraderResult]
    duration_ms: float = 0.0
    pass_threshold: float = 0.95
    error: str | None = None
    golden_set_tags: list[str] | None = None
    reducer_scores: dict[str, float] = Field(default_factory=dict)
    epoch_scores: list[float] = Field(default_factory=list)


class EvalRun(BaseModel):
    run_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    layer: Layer
    tier: Tier | None = None
    tasks_total: int = 0
    tasks_passed: int = 0
    tasks_failed: int = 0
    task_results: list[TaskResult] = Field(default_factory=list)
    overall_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    gate_result: GateResult | None = None
    baseline_run_id: str | None = None
    git_sha: str | None = None


class PostMortem(BaseModel):
    what: str
    root_cause: str
    impact: str
    fix: str
    prevention: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
