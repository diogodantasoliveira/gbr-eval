"""Grader interface and registry.

Two Protocols exist:
- ``Grader`` — deterministic graders (pure functions, no side effects).
- ``ContextAwareGrader`` — graders that receive sibling results via GraderContext
  (currently only LLMJudge). Documented exception alongside the LLM-judge non-purity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from gbr_eval.harness.models import GraderContext, GraderResult, GraderSpec

if TYPE_CHECKING:
    from collections.abc import Callable

_REGISTRY: dict[str, type[Grader]] = {}
_CONTEXT_AWARE: set[str] = set()


@runtime_checkable
class Grader(Protocol):
    def grade(
        self,
        output: dict[str, Any],
        expected: dict[str, Any],
        spec: GraderSpec,
    ) -> GraderResult: ...


class ContextAwareGrader(Protocol):
    """Graders that receive sibling results via GraderContext.

    Not ``@runtime_checkable`` — use ``register_grader(name, context_aware=True)``
    for runtime dispatch instead, since Protocol isinstance checks cannot
    distinguish method signatures that differ only in keyword arguments.
    """

    def grade(
        self,
        output: dict[str, Any],
        expected: dict[str, Any],
        spec: GraderSpec,
        *,
        context: GraderContext | None = None,
    ) -> GraderResult: ...


def register_grader(
    name: str, *, context_aware: bool = False,
) -> Callable[[type[Grader]], type[Grader]]:
    def decorator(cls: type[Grader]) -> type[Grader]:
        if name in _REGISTRY and _REGISTRY[name] is not cls:
            raise ValueError(f"Grader '{name}' already registered by {_REGISTRY[name].__name__}")
        _REGISTRY[name] = cls
        if context_aware:
            _CONTEXT_AWARE.add(name)
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
    context: GraderContext | None = None,
) -> GraderResult:
    try:
        grader = get_grader(grader_name)
        if context is not None and grader_name in _CONTEXT_AWARE:
            return grader.grade(output, expected, spec, context=context)  # type: ignore[call-arg]
        return grader.grade(output, expected, spec)
    except KeyError as exc:
        return GraderResult(
            grader_type=grader_name,
            field=spec.field,
            passed=False,
            score=0.0,
            weight=spec.weight,
            required=spec.required,
            error=f"KeyError: {exc}",
        )
    except (ValueError, TypeError, AttributeError) as exc:
        return GraderResult(
            grader_type=grader_name,
            field=spec.field,
            passed=False,
            score=0.0,
            weight=spec.weight,
            required=spec.required,
            error=f"{type(exc).__name__}: {exc}",
        )
