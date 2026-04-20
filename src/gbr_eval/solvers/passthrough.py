"""Passthrough solver — returns trace unchanged."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gbr_eval.solvers.base import register_solver

if TYPE_CHECKING:
    from gbr_eval.harness.models import TaskInput
    from gbr_eval.solvers.models import AgentTrace


@register_solver("passthrough")
class PassthroughSolver:
    async def solve(self, task_input: TaskInput, trace: AgentTrace) -> AgentTrace:
        return trace
