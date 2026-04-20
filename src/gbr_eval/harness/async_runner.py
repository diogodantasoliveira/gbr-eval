"""Async runner for solver-based eval tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from gbr_eval.harness.models import (
    Task,
    TaskResult,
)
from gbr_eval.harness.runner import (
    _all_graders_deterministic,
    _reduce_scores,
    _run_single_epoch,
)
from gbr_eval.solvers.models import AgentTrace

if TYPE_CHECKING:
    from gbr_eval.solvers.base import Solver


async def run_task_with_solver(
    task: Task,
    solver: Solver,
    *,
    model_roles: dict[str, str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> TaskResult:
    """Run a task using a solver to produce output, then grade the result."""
    trace = AgentTrace(started_at=datetime.now(UTC))
    trace = await solver.solve(task.input, trace)
    trace.finished_at = datetime.now(UTC)

    output = trace.output

    effective_epochs = 1 if (task.epochs > 1 and _all_graders_deterministic(task)) else task.epochs

    solver_metadata: dict[str, Any] = {
        "has_trace": True,
        "tool_calls_count": len(trace.tool_calls),
    }
    if extra_metadata:
        solver_metadata.update(extra_metadata)

    epoch_scores: list[float] = []
    all_grader_results = []
    total_duration = 0.0

    for _ in range(effective_epochs):
        grader_results, score, duration_ms = _run_single_epoch(
            task, output, model_roles=model_roles, extra_metadata=solver_metadata,
        )
        epoch_scores.append(score)
        all_grader_results.extend(grader_results)
        total_duration += duration_ms

    total_duration += trace.latency_ms

    reducer_scores = {
        r.value: _reduce_scores(epoch_scores, r, task.pass_threshold)
        for r in task.reducers
    }
    primary_score = reducer_scores[task.primary_reducer.value]
    any_required_failed = any(r.required and not r.passed for r in all_grader_results)
    passed = primary_score >= task.pass_threshold and not any_required_failed

    return TaskResult(
        task_id=task.task_id,
        passed=passed,
        score=primary_score,
        grader_results=all_grader_results,
        duration_ms=total_duration,
        pass_threshold=task.pass_threshold,
        reducer_scores=reducer_scores,
        epoch_scores=epoch_scores,
    )
