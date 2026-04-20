"""Engineering-layer graders — analyze code for convention violations."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from gbr_eval.graders._shared import _is_catastrophic_pattern, _make_result
from gbr_eval.graders.base import register_grader

if TYPE_CHECKING:
    from gbr_eval.harness.models import GraderResult, GraderSpec

_MAX_PATTERN_LEN = 1_000
_MAX_INPUT_LEN = 100_000


@register_grader("pattern_required")
class PatternRequired:
    """Check that required patterns exist in code output.

    Config:
        pattern: regex pattern that MUST be found
        file_key: key in output containing code/file content (default: "content")
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        pattern = spec.config.get("pattern", "")
        if not pattern:
            return _make_result(spec, False, 0.0, "No pattern specified in config")

        if len(pattern) > _MAX_PATTERN_LEN:
            return _make_result(spec, False, 0.0, f"Pattern too long ({len(pattern)} > {_MAX_PATTERN_LEN})")

        if _is_catastrophic_pattern(pattern):
            return _make_result(spec, False, 0.0, f"Potentially catastrophic regex pattern rejected: {pattern}")

        file_key = spec.config.get("file_key", "content")
        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        try:
            matches = re.findall(pattern, content, re.MULTILINE)
        except re.error as e:
            return _make_result(spec, False, 0.0, f"Invalid regex pattern: {e}")

        if matches:
            return _make_result(spec, True, 1.0, f"Pattern found ({len(matches)} matches)")
        return _make_result(spec, False, 0.0, f"Required pattern not found: {pattern}")


@register_grader("pattern_forbidden")
class PatternForbidden:
    """Check that forbidden patterns do NOT exist in code output.

    Config:
        pattern: regex pattern that MUST NOT be found
        file_key: key in output containing code/file content (default: "content")
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        pattern = spec.config.get("pattern", "")
        if not pattern:
            return _make_result(spec, False, 0.0, "No pattern specified in config")

        if len(pattern) > _MAX_PATTERN_LEN:
            return _make_result(spec, False, 0.0, f"Pattern too long ({len(pattern)} > {_MAX_PATTERN_LEN})")

        if _is_catastrophic_pattern(pattern):
            return _make_result(spec, False, 0.0, f"Potentially catastrophic regex pattern rejected: {pattern}")

        file_key = spec.config.get("file_key", "content")
        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        try:
            matches = re.findall(pattern, content, re.MULTILINE)
        except re.error as e:
            return _make_result(spec, False, 0.0, f"Invalid regex pattern: {e}")

        if matches:
            return _make_result(spec, False, 0.0, f"Forbidden pattern found ({len(matches)} matches): {pattern}")
        return _make_result(spec, True, 1.0, "No forbidden patterns found")


@register_grader("convention_check")
class ConventionCheck:
    """Check multiple convention rules against code output.

    Config:
        rules: list of {pattern, type ("required"|"forbidden"), description}
        file_key: key in output (default: "content")
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        rules = spec.config.get("rules", [])
        if not rules:
            return _make_result(spec, False, 0.0, "No rules specified")

        file_key = spec.config.get("file_key", "content")
        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        violations: list[str] = []
        for rule in rules:
            pattern = rule.get("pattern", "")
            rule_type = rule.get("type", "required")
            desc = rule.get("description", pattern)

            if len(pattern) > _MAX_PATTERN_LEN:
                violations.append(f"SKIP: {desc} (pattern too long)")
                continue

            if _is_catastrophic_pattern(pattern):
                violations.append(f"SKIP: {desc} (catastrophic regex pattern)")
                continue

            try:
                matches = re.findall(pattern, content, re.MULTILINE)
            except re.error as e:
                violations.append(f"ERROR: {desc} (invalid regex: {e})")
                continue

            if rule_type == "required" and not matches:
                violations.append(f"MISSING: {desc}")
            elif rule_type == "forbidden" and matches:
                violations.append(f"FOUND: {desc} ({len(matches)}x)")

        if violations:
            score = max(0.0, 1.0 - len(violations) / len(rules))
            return _make_result(spec, False, score, "; ".join(violations))
        return _make_result(spec, True, 1.0, f"All {len(rules)} convention rules pass")
