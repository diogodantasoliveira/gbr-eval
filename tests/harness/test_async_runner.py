"""Tests for async runner with solver pattern."""

from __future__ import annotations

import asyncio

import pytest

import gbr_eval.graders  # noqa: F401
from gbr_eval.harness.async_runner import run_task_with_solver
from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.solvers.models import AgentTrace, ToolCall


def _make_task(**kwargs: object) -> Task:
    defaults: dict[str, object] = {
        "task_id": "test.solver",
        "category": Category.EXTRACTION,
        "component": "test",
        "layer": Layer.PRODUCT,
        "tier": Tier.GATE,
        "input": TaskInput(),
        "expected": {"cpf": "123.456.789-09"},
        "graders": [
            GraderSpec(type="exact_match", field="cpf", weight=1.0),
        ],
        "scoring_mode": ScoringMode.WEIGHTED,
        "pass_threshold": 0.95,
    }
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


class _OutputSolver:
    """Test solver that sets output from a pre-defined dict."""

    def __init__(self, output: dict[str, object]) -> None:
        self._output = output

    async def solve(self, task_input: TaskInput, trace: AgentTrace) -> AgentTrace:
        return trace.model_copy(update={
            "output": self._output,
            "tool_calls": [ToolCall(tool_name="test_tool", arguments={"key": "val"})],
        })


class TestRunTaskWithSolver:
    def test_passthrough_with_output(self) -> None:
        task = _make_task()
        trace = AgentTrace(output={"cpf": "123.456.789-09"})

        class PreloadedSolver:
            async def solve(self, task_input: TaskInput, t: AgentTrace) -> AgentTrace:
                return t.model_copy(update={"output": trace.output})

        result = asyncio.run(run_task_with_solver(task, PreloadedSolver()))
        assert result.passed
        assert result.score == 1.0

    def test_failing_output(self) -> None:
        task = _make_task()
        solver = _OutputSolver({"cpf": "wrong"})
        result = asyncio.run(run_task_with_solver(task, solver))
        assert not result.passed
        assert result.score == 0.0

    def test_result_has_epoch_and_reducer_scores(self) -> None:
        task = _make_task()
        solver = _OutputSolver({"cpf": "123.456.789-09"})
        result = asyncio.run(run_task_with_solver(task, solver))
        assert len(result.epoch_scores) == 1
        assert "mean" in result.reducer_scores

    def test_duration_includes_trace_latency(self) -> None:
        task = _make_task()

        class SlowSolver:
            async def solve(self, task_input: TaskInput, trace: AgentTrace) -> AgentTrace:
                return trace.model_copy(update={
                    "output": {"cpf": "123.456.789-09"},
                    "latency_ms": 5000.0,
                })

        result = asyncio.run(run_task_with_solver(task, SlowSolver()))
        assert result.duration_ms >= 5000.0

    def test_model_roles_threaded(self) -> None:
        task = _make_task()
        solver = _OutputSolver({"cpf": "123.456.789-09"})
        result = asyncio.run(
            run_task_with_solver(task, solver, model_roles={"grader": "test-model"})
        )
        assert result.passed

    def test_multiple_graders(self) -> None:
        task = _make_task(
            expected={"cpf": "123", "nome": "Joao"},
            graders=[
                GraderSpec(type="exact_match", field="cpf", weight=1.0),
                GraderSpec(type="exact_match", field="nome", weight=1.0),
            ],
        )
        solver = _OutputSolver({"cpf": "123", "nome": "Joao"})
        result = asyncio.run(run_task_with_solver(task, solver))
        assert result.passed
        assert len(result.grader_results) == 2

    def test_context_accumulated_across_graders(self) -> None:
        task = _make_task(
            expected={"cpf": "123", "nome": "Joao"},
            graders=[
                GraderSpec(type="exact_match", field="cpf", weight=1.0),
                GraderSpec(type="exact_match", field="nome", weight=1.0),
            ],
        )
        solver = _OutputSolver({"cpf": "wrong", "nome": "Joao"})
        result = asyncio.run(run_task_with_solver(task, solver))
        assert not result.grader_results[0].passed
        assert result.grader_results[1].passed

    def test_deterministic_short_circuit_in_solver(self) -> None:
        """epochs=3 with only deterministic graders must short-circuit to 1 epoch."""
        from gbr_eval.harness.models import ScoreReducer
        task = _make_task(
            epochs=3,
            reducers=[ScoreReducer.MEAN],
            primary_reducer=ScoreReducer.MEAN,
        )
        solver = _OutputSolver({"cpf": "123.456.789-09"})
        result = asyncio.run(run_task_with_solver(task, solver))
        assert len(result.epoch_scores) == 1

    def test_solver_extra_metadata_in_context(self) -> None:
        """has_trace and tool_calls_count must be present in grader context metadata."""
        captured_contexts: list[object] = []

        import gbr_eval.graders.base as _base
        from gbr_eval.graders.base import _REGISTRY, register_grader
        from gbr_eval.harness.models import GraderResult as _GraderResult

        _spy_name = "__spy_context_grader__"

        @register_grader(_spy_name, context_aware=True)
        class _SpyGrader:
            def grade(self, output, expected, spec, *, context=None):  # noqa: ANN001
                if context is not None:
                    captured_contexts.append(context.metadata)
                return _GraderResult(
                    grader_type=_spy_name,
                    field=spec.field,
                    passed=True,
                    score=1.0,
                    weight=spec.weight,
                    required=spec.required,
                )

        try:
            task = _make_task(
                graders=[GraderSpec(type=_spy_name, field="cpf", weight=1.0)],
                expected={},
            )
            solver = _OutputSolver({"cpf": "123.456.789-09"})
            asyncio.run(run_task_with_solver(task, solver))
            assert len(captured_contexts) >= 1
            meta = captured_contexts[0]
            assert "has_trace" in meta
            assert "tool_calls_count" in meta
        finally:
            _REGISTRY.pop(_spy_name, None)
            _base._CONTEXT_AWARE.discard(_spy_name)

    def test_solver_exception_propagates(self) -> None:
        """A solver that raises RuntimeError must not be silently swallowed."""
        task = _make_task()

        class _ErrorSolver:
            async def solve(self, task_input: TaskInput, trace: AgentTrace) -> AgentTrace:
                raise RuntimeError("solver failed")

        with pytest.raises(RuntimeError, match="solver failed"):
            asyncio.run(run_task_with_solver(task, _ErrorSolver()))
