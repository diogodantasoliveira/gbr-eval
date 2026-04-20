"""Solver protocol and registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from gbr_eval.harness.models import TaskInput
    from gbr_eval.solvers.models import AgentTrace

_SOLVER_REGISTRY: dict[str, type[Solver]] = {}


class Solver(Protocol):
    async def solve(self, task_input: TaskInput, trace: AgentTrace) -> AgentTrace: ...


def register_solver(name: str) -> Callable[[type[Solver]], type[Solver]]:
    def decorator(cls: type[Solver]) -> type[Solver]:
        if name in _SOLVER_REGISTRY and _SOLVER_REGISTRY[name] is not cls:
            raise ValueError(f"Solver '{name}' already registered by {_SOLVER_REGISTRY[name].__name__}")
        _SOLVER_REGISTRY[name] = cls
        return cls
    return decorator


def get_solver(name: str) -> Solver:
    if name not in _SOLVER_REGISTRY:
        raise KeyError(f"Unknown solver: {name}. Available: {sorted(_SOLVER_REGISTRY)}")
    return _SOLVER_REGISTRY[name]()
