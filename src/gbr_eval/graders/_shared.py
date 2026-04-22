"""Shared utilities for grader implementations."""

from __future__ import annotations

import json
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


def _strip_markdown_fence(text: str) -> str:
    """Remove markdown code fences wrapping a JSON response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
    return text


def _extract_json(text: str) -> str:
    """Extract JSON object from LLM response text, handling mixed prose+JSON.

    Strategies attempted in order:
    1. Direct parse after stripping markdown fences.
    2. Find first ``{`` and match braces to locate the outermost object.
    """
    cleaned = _strip_markdown_fence(text)
    try:
        json.loads(cleaned)
        return cleaned
    except (json.JSONDecodeError, ValueError):
        pass
    brace_start = cleaned.find("{")
    if brace_start == -1:
        return cleaned
    depth = 0
    for i in range(brace_start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                return cleaned[brace_start : i + 1]
    return cleaned[brace_start:]
