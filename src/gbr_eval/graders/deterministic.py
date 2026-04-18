"""Deterministic graders — pure functions, 100% reproducible."""

from __future__ import annotations

import re
from typing import Any

from gbr_eval.graders.base import register_grader
from gbr_eval.harness.models import GraderResult, GraderSpec


def _get_field(data: dict[str, Any], path: str) -> Any:
    """Traverse dotted path (e.g. 'citation.cpf') into nested dict."""
    current: Any = data
    for key in path.split("."):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


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


@register_grader("exact_match")
class ExactMatch:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        reference = _get_field(expected, field)

        case_sensitive = spec.config.get("case_sensitive", True)
        if not case_sensitive and isinstance(actual, str) and isinstance(reference, str):
            passed = actual.lower() == reference.lower()
        else:
            passed = actual == reference

        score = 1.0 if passed else 0.0
        details = f"expected={reference!r}, got={actual!r}"
        return _make_result(spec, passed, score, details)


@register_grader("numeric_range")
class NumericRange:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        if actual is None:
            return _make_result(spec, False, 0.0, f"Field '{field}' not found in output")

        try:
            value = float(actual)
        except (ValueError, TypeError):
            return _make_result(spec, False, 0.0, f"Non-numeric value: {actual!r}")

        min_val = spec.config.get("min")
        max_val = spec.config.get("max")

        if min_val is not None and value < float(min_val):
            return _make_result(spec, False, 0.0, f"{value} < min {min_val}")
        if max_val is not None and value > float(max_val):
            return _make_result(spec, False, 0.0, f"{value} > max {max_val}")

        return _make_result(spec, True, 1.0, f"{value} within [{min_val}, {max_val}]")


@register_grader("numeric_tolerance")
class NumericTolerance:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        reference = _get_field(expected, field)

        if actual is None or reference is None:
            return _make_result(spec, False, 0.0, f"Missing field: actual={actual}, expected={reference}")

        try:
            actual_f, ref_f = float(actual), float(reference)
        except (ValueError, TypeError):
            return _make_result(spec, False, 0.0, f"Non-numeric: actual={actual!r}, expected={reference!r}")

        tolerance = float(spec.config.get("tolerance", 0.01))
        diff = abs(actual_f - ref_f)
        max_diff = abs(ref_f * tolerance) if ref_f != 0 else tolerance

        passed = diff <= max_diff
        score = max(0.0, 1.0 - (diff / max_diff)) if max_diff > 0 else (1.0 if diff == 0 else 0.0)
        details = f"diff={diff:.6f}, tolerance={max_diff:.6f} ({tolerance*100}%)"
        return _make_result(spec, passed, score, details)


@register_grader("regex_match")
class RegexMatch:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        if actual is None:
            return _make_result(spec, False, 0.0, f"Field '{field}' not found")

        pattern = spec.config.get("pattern", "")
        if not pattern:
            return _make_result(spec, False, 0.0, "No pattern configured")

        matched = bool(re.search(pattern, str(actual)))
        details = f"pattern={pattern!r}, value={str(actual)!r}"
        return _make_result(spec, matched, 1.0 if matched else 0.0, details)


@register_grader("field_not_empty")
class FieldNotEmpty:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        not_empty = actual is not None and actual != "" and actual != [] and actual != {}
        details = f"value={actual!r}" if not not_empty else "present"
        return _make_result(spec, not_empty, 1.0 if not_empty else 0.0, details)


@register_grader("set_membership")
class SetMembership:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        valid_set: list[Any] = spec.config.get("valid_values", [])

        if not valid_set:
            return _make_result(spec, False, 0.0, "No valid_values configured")

        passed = actual in valid_set
        details = f"value={actual!r}, valid={valid_set!r}"
        return _make_result(spec, passed, 1.0 if passed else 0.0, details)


@register_grader("string_contains")
class StringContains:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        if actual is None:
            return _make_result(spec, False, 0.0, f"Field '{field}' not found")

        substring = spec.config.get("substring", "")
        if not substring:
            substring_ref = _get_field(expected, field)
            if substring_ref:
                substring = str(substring_ref)

        if not substring:
            return _make_result(spec, False, 0.0, "No substring to check")

        case_sensitive = spec.config.get("case_sensitive", True)
        haystack = str(actual)
        needle = str(substring)

        if not case_sensitive:
            haystack = haystack.lower()
            needle = needle.lower()

        passed = needle in haystack
        details = f"substring={needle!r} in value"
        return _make_result(spec, passed, 1.0 if passed else 0.0, details)
