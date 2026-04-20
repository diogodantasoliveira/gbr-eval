"""Shared utilities for grader implementations."""

from __future__ import annotations

import re

from gbr_eval.harness.models import GraderResult, GraderSpec

_CATASTROPHIC_RE = re.compile(r"(\([^)]*[+*][^)]*\))[+*]")


def _is_catastrophic_pattern(pattern: str) -> bool:
    """Detect obvious catastrophic backtracking patterns like (a+)+."""
    return bool(_CATASTROPHIC_RE.search(pattern))


def _make_result(spec: GraderSpec, passed: bool, score: float, details: str) -> GraderResult:
    return GraderResult(
        grader_type=spec.type,
        field=spec.field,
        passed=passed,
        score=score,
        weight=spec.weight,
        required=spec.required,
        details=details,
    )
