"""Grader interface and registry."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from gbr_eval.harness.models import GraderResult, GraderSpec

_REGISTRY: dict[str, type[Grader]] = {}


@runtime_checkable
class Grader(Protocol):
    def grade(
        self,
        output: dict[str, Any],
        expected: dict[str, Any],
        spec: GraderSpec,
    ) -> GraderResult: ...


def register_grader(name: str):
    def decorator(cls: type[Grader]):
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_grader(name: str) -> Grader:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown grader: {name}. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[name]()


def grade(
    grader_name: str,
    output: dict[str, Any],
    expected: dict[str, Any],
    spec: GraderSpec,
) -> GraderResult:
    grader = get_grader(grader_name)
    try:
        return grader.grade(output, expected, spec)
    except Exception as exc:
        return GraderResult(
            grader_type=grader_name,
            field=spec.field,
            passed=False,
            score=0.0,
            weight=spec.weight,
            required=spec.required,
            error=str(exc),
        )
