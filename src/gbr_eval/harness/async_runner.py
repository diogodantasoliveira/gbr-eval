"""Async runner for solver-based eval tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from gbr_eval.harness.runner import _compute_task_result
from gbr_eval.solvers.models import AgentTrace

if TYPE_CHECKING:
    from gbr_eval.harness.models import Task, TaskResult
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

    solver_metadata: dict[str, Any] = {
        "has_trace": True,
        "tool_calls_count": len(trace.tool_calls),
    }
    if extra_metadata:
        solver_metadata.update(extra_metadata)

    return _compute_task_result(
        task,
        trace.output,
        model_roles=model_roles,
        extra_metadata=solver_metadata,
        extra_duration_ms=trace.latency_ms,
    )
