"""Tests for GraderContext (Pattern 4 from inspect_ai)."""

from __future__ import annotations

import gbr_eval.graders  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import (
    Category,
    GraderContext,
    GraderResult,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.runner import run_task


def _make_task(**kwargs: object) -> Task:
    defaults: dict[str, object] = {
        "task_id": "test.context",
        "category": Category.EXTRACTION,
        "component": "test",
        "layer": Layer.PRODUCT,
        "tier": Tier.GATE,
        "input": TaskInput(),
        "expected": {"cpf": "123.456.789-09", "nome": "João"},
        "graders": [
            GraderSpec(type="exact_match", field="cpf", weight=3.0),
            GraderSpec(type="exact_match", field="nome", weight=1.0),
        ],
        "scoring_mode": ScoringMode.WEIGHTED,
        "pass_threshold": 0.95,
    }
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


# --- GraderContext model ---


class TestGraderContextModel:
    def test_default_empty(self) -> None:
        ctx = GraderContext()
        assert ctx.metadata == {}
        assert ctx.previous_results == []

    def test_with_metadata(self) -> None:
        ctx = GraderContext(metadata={"task_id": "test.1", "tenant_profile": "global"})
        assert ctx.metadata["task_id"] == "test.1"

    def test_accumulates_results(self) -> None:
        r1 = GraderResult(grader_type="exact_match", field="cpf", passed=True, score=1.0)
        r2 = GraderResult(grader_type="exact_match", field="nome", passed=False, score=0.0)
        ctx = GraderContext(previous_results=[r1])
        ctx2 = ctx.model_copy(update={"previous_results": [*ctx.previous_results, r2]})
        assert len(ctx.previous_results) == 1
        assert len(ctx2.previous_results) == 2

    def test_serialization_roundtrip(self) -> None:
        r = GraderResult(grader_type="exact_match", field="cpf", passed=True, score=1.0)
        ctx = GraderContext(metadata={"key": "val"}, previous_results=[r])
        data = ctx.model_dump()
        restored = GraderContext.model_validate(data)
        assert restored.metadata == {"key": "val"}
        assert len(restored.previous_results) == 1


# --- Deterministic graders with context ---


class TestDeterministicWithContext:
    def test_exact_match_ignores_context(self) -> None:
        spec = GraderSpec(type="exact_match", field="cpf")
        ctx = GraderContext(metadata={"task_id": "test"})
        result = grade("exact_match", {"cpf": "123"}, {"cpf": "123"}, spec, context=ctx)
        assert result.passed

    def test_field_f1_ignores_context(self) -> None:
        spec = GraderSpec(type="field_f1", field="nome")
        ctx = GraderContext(metadata={"task_id": "test"})
        result = grade("field_f1", {"nome": "João Silva"}, {"nome": "João Silva"}, spec, context=ctx)
        assert result.passed

    def test_numeric_range_ignores_context(self) -> None:
        spec = GraderSpec(type="numeric_range", field="valor", config={"min": 10, "max": 100})
        ctx = GraderContext(metadata={"task_id": "test"})
        result = grade("numeric_range", {"valor": 50}, {"valor": 50}, spec, context=ctx)
        assert result.passed

    def test_all_deterministic_graders_work_with_context(self) -> None:
        deterministic_graders = [
            ("exact_match", GraderSpec(type="exact_match", field="x"), {"x": "a"}, {"x": "a"}),
            ("field_not_empty", GraderSpec(type="field_not_empty", field="x"), {"x": "val"}, {}),
            ("field_f1", GraderSpec(type="field_f1", field="x"), {"x": "hello"}, {"x": "hello"}),
            (
                "numeric_range",
                GraderSpec(type="numeric_range", field="x", config={"min": 0, "max": 10}),
                {"x": 5},
                {"x": 5},
            ),
        ]
        ctx = GraderContext(metadata={"task_id": "test"})
        for name, spec, output, expected in deterministic_graders:
            result = grade(name, output, expected, spec, context=ctx)
            assert result.passed, f"{name} failed with context"

    def test_grade_without_context_still_works(self) -> None:
        spec = GraderSpec(type="exact_match", field="cpf")
        result = grade("exact_match", {"cpf": "123"}, {"cpf": "123"}, spec)
        assert result.passed


# --- run_task context accumulation ---


class TestRunTaskContext:
    def test_context_ordering_in_results(self) -> None:
        task = _make_task()
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert result.grader_results[0].field == "cpf"
        assert result.grader_results[1].field == "nome"

    def test_context_includes_task_metadata(self) -> None:
        task = _make_task()
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert result.passed
        assert len(result.grader_results) == 2

    def test_context_immutable_per_grader(self) -> None:
        task = _make_task(
            graders=[
                GraderSpec(type="exact_match", field="cpf", weight=1.0),
                GraderSpec(type="exact_match", field="nome", weight=1.0),
            ],
        )
        output = {"cpf": "wrong", "nome": "João"}
        result = run_task(task, output)
        assert not result.grader_results[0].passed
        assert result.grader_results[1].passed
