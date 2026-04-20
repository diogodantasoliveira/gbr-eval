"""Tests for solver registry and passthrough solver."""

from __future__ import annotations

import asyncio

import pytest

import gbr_eval.solvers.passthrough  # noqa: F401 — trigger registration
from gbr_eval.harness.models import TaskInput
from gbr_eval.solvers.base import _SOLVER_REGISTRY, get_solver, register_solver
from gbr_eval.solvers.models import AgentTrace


class TestSolverRegistry:
    def test_passthrough_registered(self) -> None:
        assert "passthrough" in _SOLVER_REGISTRY

    def test_get_solver_passthrough(self) -> None:
        solver = get_solver("passthrough")
        assert solver is not None

    def test_get_solver_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown solver"):
            get_solver("nonexistent_solver")

    def test_register_duplicate_different_class_raises(self) -> None:
        with pytest.raises(ValueError, match="already registered"):

            @register_solver("passthrough")
            class _Dup:  # noqa: N801
                async def solve(self, task_input: object, trace: AgentTrace) -> AgentTrace:
                    return trace


class TestPassthroughSolver:
    def test_returns_trace_unchanged(self) -> None:
        solver = get_solver("passthrough")
        trace = AgentTrace(output={"cpf": "123"}, cost_usd=0.01)
        task_input = TaskInput()
        result = asyncio.run(solver.solve(task_input, trace))
        assert result.output == {"cpf": "123"}
        assert result.cost_usd == 0.01

    def test_empty_trace(self) -> None:
        solver = get_solver("passthrough")
        trace = AgentTrace()
        task_input = TaskInput()
        result = asyncio.run(solver.solve(task_input, trace))
        assert result.output == {}
        assert result.messages == []
