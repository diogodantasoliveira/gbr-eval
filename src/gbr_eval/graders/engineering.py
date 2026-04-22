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


def _count_context_filtered_matches(
    content: str,
    pattern: str,
    exclude_context: str | None,
    require_context: str | None,
) -> int:
    """Count matches of *pattern* in *content*, applying line-level context filters.

    When neither *exclude_context* nor *require_context* is set the function
    falls back to a simple ``re.findall`` for backward-compatible performance.

    For each match the containing line is tested:
    - If *exclude_context* matches the line the hit is discarded.
    - If *require_context* does NOT match the line the hit is discarded.
    """
    if not exclude_context and not require_context:
        return len(re.findall(pattern, content, re.MULTILINE))

    # Validate context patterns early so callers get clear errors.
    if exclude_context:
        re.compile(exclude_context)
    if require_context:
        re.compile(require_context)

    surviving = 0
    for line in content.splitlines():
        if not re.search(pattern, line):
            continue
        if exclude_context and re.search(exclude_context, line):
            continue
        if require_context and not re.search(require_context, line):
            continue
        # Count all matches on this surviving line.
        surviving += len(re.findall(pattern, line))
    return surviving


@register_grader("pattern_required")
class PatternRequired:
    """Check that required patterns exist in code output.

    Config:
        pattern: regex pattern that MUST be found
        file_key: key in output containing code/file content (default: "content")
        exclude_context: regex — ignore matches on lines matching this pattern
        require_context: regex — only count matches on lines matching this pattern
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        pattern = spec.config.get("pattern", "")
        if not pattern:
            return _make_result(spec, False, 0.0, "No pattern specified in config")

        if len(pattern) > _MAX_PATTERN_LEN:
            return _make_result(spec, False, 0.0, f"Pattern too long ({len(pattern)} > {_MAX_PATTERN_LEN})")

        if _is_catastrophic_pattern(pattern):
            return _make_result(spec, False, 0.0, f"Potentially catastrophic regex pattern rejected: {pattern}")

        exclude_context: str | None = spec.config.get("exclude_context")
        require_context: str | None = spec.config.get("require_context")

        file_key = spec.config.get("file_key", "content")
        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        try:
            match_count = _count_context_filtered_matches(
                content, pattern, exclude_context, require_context,
            )
        except re.error as e:
            return _make_result(spec, False, 0.0, f"Invalid regex pattern: {e}")

        if match_count:
            return _make_result(spec, True, 1.0, f"Pattern found ({match_count} matches)")
        return _make_result(spec, False, 0.0, f"Required pattern not found: {pattern}")


@register_grader("pattern_forbidden")
class PatternForbidden:
    """Check that forbidden patterns do NOT exist in code output.

    Config:
        pattern: regex pattern that MUST NOT be found
        file_key: key in output containing code/file content (default: "content")
        exclude_context: regex — ignore matches on lines matching this pattern
        require_context: regex — only flag matches on lines matching this pattern
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        pattern = spec.config.get("pattern", "")
        if not pattern:
            return _make_result(spec, False, 0.0, "No pattern specified in config")

        if len(pattern) > _MAX_PATTERN_LEN:
            return _make_result(spec, False, 0.0, f"Pattern too long ({len(pattern)} > {_MAX_PATTERN_LEN})")

        if _is_catastrophic_pattern(pattern):
            return _make_result(spec, False, 0.0, f"Potentially catastrophic regex pattern rejected: {pattern}")

        exclude_context: str | None = spec.config.get("exclude_context")
        require_context: str | None = spec.config.get("require_context")

        file_key = spec.config.get("file_key", "content")
        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        try:
            match_count = _count_context_filtered_matches(
                content, pattern, exclude_context, require_context,
            )
        except re.error as e:
            return _make_result(spec, False, 0.0, f"Invalid regex pattern: {e}")

        if match_count:
            return _make_result(spec, False, 0.0, f"Forbidden pattern found ({match_count} matches): {pattern}")
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


_DEFAULT_FINANCIAL_TERMS = (
    r"price|amount|total|cost|valor|fee|markup|discount|saldo|tarifa|billing|charge|payment|invoice"
)
_DEFAULT_FORBIDDEN_FLOAT_PATTERNS: list[str] = [
    r":\s*float\b",
    r"float\(",
]
_DEFAULT_REQUIRED_DECIMAL_PATTERNS: list[str] = [
    r"from decimal import Decimal|import decimal|Decimal\(",
]
# Matches a bare float literal assignment: = <digits>.<digits>
# Applied line-by-line together with financial term detection.
_FLOAT_LITERAL_RE = re.compile(r"=\s*\d+\.\d+")


@register_grader("decimal_usage")
class DecimalUsage:
    """Context-aware grader: checks Decimal vs float usage only in financial files.

    For files that contain no financial terms the grader auto-passes (skipped).
    For files with financial context it verifies:
    - No forbidden float patterns (type annotations, explicit casts, financial float literals)
    - If float-typed values are present, Decimal must be imported / used

    Config:
        file_key: key in output dict (default "content")
        financial_terms: pipe-separated regex alternation of terms (default built-in list)
        forbidden_float_patterns: list of regex strings to forbid
        required_decimal_patterns: list of regex strings that must be present when float
            forbidden violations exist
        skip_if_no_context: bool — auto-pass non-financial files (default True)
    """

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        file_key = spec.config.get("file_key", "content")
        content = output.get(file_key, "")
        if not isinstance(content, str):
            content = str(content)
        content = content[:_MAX_INPUT_LEN]

        skip_if_no_context: bool = spec.config.get("skip_if_no_context", True)

        # --- build financial_terms pattern ---
        financial_terms_raw: str = spec.config.get("financial_terms", _DEFAULT_FINANCIAL_TERMS)
        if len(financial_terms_raw) > _MAX_PATTERN_LEN:
            msg = f"financial_terms pattern too long ({len(financial_terms_raw)} > {_MAX_PATTERN_LEN})"
            return _make_result(spec, False, 0.0, msg)
        if _is_catastrophic_pattern(financial_terms_raw):
            msg = f"Potentially catastrophic regex in financial_terms rejected: {financial_terms_raw}"
            return _make_result(spec, False, 0.0, msg)

        # --- build forbidden patterns list ---
        forbidden_raw: list[str] = spec.config.get("forbidden_float_patterns", _DEFAULT_FORBIDDEN_FLOAT_PATTERNS)
        for fp in forbidden_raw:
            if len(fp) > _MAX_PATTERN_LEN:
                return _make_result(spec, False, 0.0, f"forbidden_float_patterns entry too long: {fp[:80]}")
            if _is_catastrophic_pattern(fp):
                msg = f"Potentially catastrophic regex in forbidden_float_patterns rejected: {fp}"
                return _make_result(spec, False, 0.0, msg)

        # --- build required patterns list ---
        required_raw: list[str] = spec.config.get("required_decimal_patterns", _DEFAULT_REQUIRED_DECIMAL_PATTERNS)
        for rp in required_raw:
            if len(rp) > _MAX_PATTERN_LEN:
                return _make_result(spec, False, 0.0, f"required_decimal_patterns entry too long: {rp[:80]}")
            if _is_catastrophic_pattern(rp):
                msg = f"Potentially catastrophic regex in required_decimal_patterns rejected: {rp}"
                return _make_result(spec, False, 0.0, msg)

        # --- detect financial context ---
        try:
            has_financial_context = bool(re.search(financial_terms_raw, content, re.IGNORECASE))
        except re.error as exc:
            return _make_result(spec, False, 0.0, f"Invalid financial_terms regex: {exc}")

        if not has_financial_context and skip_if_no_context:
            return _make_result(spec, True, 1.0, "No financial context detected (skipped)")

        # --- check forbidden patterns (type annotations + explicit casts) ---
        violations: list[str] = []

        for fp in forbidden_raw:
            try:
                matches = re.findall(fp, content, re.MULTILINE)
            except re.error as exc:
                return _make_result(spec, False, 0.0, f"Invalid forbidden pattern '{fp}': {exc}")
            if matches:
                violations.append(f"Forbidden float usage ({len(matches)}x): {fp}")

        # --- check float literal assignments on financial lines ---
        lines = content.splitlines()
        try:
            financial_re = re.compile(financial_terms_raw, re.IGNORECASE)
        except re.error as exc:
            return _make_result(spec, False, 0.0, f"Invalid financial_terms regex: {exc}")

        financial_float_literal_lines: list[int] = []
        for lineno, line in enumerate(lines, start=1):
            if _FLOAT_LITERAL_RE.search(line) and financial_re.search(line):
                financial_float_literal_lines.append(lineno)

        if financial_float_literal_lines:
            line_list = ", ".join(str(n) for n in financial_float_literal_lines)
            violations.append(f"Float literal on financial line(s): {line_list}")

        if violations:
            return _make_result(spec, False, 0.0, "; ".join(violations))

        # --- no forbidden issues found --- pass regardless of Decimal presence ---
        return _make_result(spec, True, 1.0, "Decimal usage check passed")
