"""Core data models for the eval harness."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Layer(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


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


class ScoringMode(StrEnum):
    WEIGHTED = "weighted"
    BINARY = "binary"
    HYBRID = "hybrid"


class GraderSpec(BaseModel):
    type: str
    field: str | None = None
    weight: float = 1.0
    required: bool = False
    config: dict[str, Any] = Field(default_factory=dict)


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
    pass_threshold: float = 0.95


class GraderResult(BaseModel):
    grader_type: str
    field: str | None = None
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    weight: float = 1.0
    required: bool = False
    details: str = ""
    error: str | None = None


class TaskResult(BaseModel):
    task_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    grader_results: list[GraderResult]
    duration_ms: float = 0.0
    error: str | None = None


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
