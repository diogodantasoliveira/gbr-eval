"""Graders for Caixa BPO eval — deterministic, pure functions."""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING, Any

from gbr_eval.graders._shared import _make_result
from gbr_eval.graders.base import register_grader

if TYPE_CHECKING:
    from gbr_eval.harness.models import GraderResult, GraderSpec

_MISSING = object()


def _get_field(data: dict[str, Any], path: str) -> Any:
    """Traverse dotted path (e.g. 'citation.cpf') into nested dict.

    Returns _MISSING sentinel when the path does not exist (vs None when field exists but is null).
    """
    current: Any = data
    for key in path.split("."):
        if isinstance(current, dict):
            if key not in current:
                return _MISSING
            current = current[key]
        else:
            return _MISSING
    return current


def _normalize_name(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode()
    lower = ascii_text.lower().strip()
    return " ".join(lower.split())


def _jaro_winkler(s1: str, s2: str) -> float:
    """Compute Jaro-Winkler similarity between two strings."""
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_window = max(len1, len2) // 2 - 1
    if match_window < 0:
        match_window = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_window)
        end = min(i + match_window + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (
        matches / len1 + matches / len2 + (matches - transpositions / 2) / matches
    ) / 3.0

    prefix_len = 0
    for i in range(min(4, len1, len2)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + prefix_len * 0.1 * (1.0 - jaro)


@register_grader("checklist_completeness")
class ChecklistCompleteness:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        checklist_field = spec.config.get("checklist_field", "checklist")
        status_field = spec.config.get("status_field", "status")
        unevaluated_values: list[Any] = spec.config.get(
            "unevaluated_values", ["pendente", "nao_avaliado", None]
        )

        checklist = _get_field(output, checklist_field)
        if checklist is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{checklist_field}' not found in output")

        if not isinstance(checklist, list):
            return _make_result(spec, False, 0.0, f"Field '{checklist_field}' is not an array")

        total = len(checklist)
        if total == 0:
            return _make_result(spec, False, 0.0, "Checklist is empty")

        evaluated = 0
        for item in checklist:
            status = item.get(status_field, _MISSING) if isinstance(item, dict) else _MISSING
            if status is not _MISSING and status not in unevaluated_values:
                evaluated += 1

        score = evaluated / total
        passed = score >= 1.0
        details = f"evaluated={evaluated}/{total}"
        return _make_result(spec, passed, score, details)


@register_grader("multi_step_calculation")
class MultiStepCalculation:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        steps_field = spec.config.get("steps_field", "steps")
        tolerance = float(spec.config.get("tolerance", 0.01))

        steps = _get_field(output, steps_field)
        if steps is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{steps_field}' not found in output")

        if not isinstance(steps, list):
            return _make_result(spec, False, 0.0, f"Field '{steps_field}' is not an array")

        total_steps = len(steps)
        if total_steps == 0:
            return _make_result(spec, False, 0.0, "Steps array is empty")

        steps_passed = 0
        for step in steps:
            if not isinstance(step, dict):
                continue
            try:
                exp_val = float(step.get("expected", 0))
                act_val = float(step.get("actual", 0))
            except (ValueError, TypeError):
                continue

            max_diff = abs(exp_val * tolerance) if exp_val != 0 else tolerance
            if abs(act_val - exp_val) <= max_diff:
                steps_passed += 1

        score = steps_passed / total_steps
        passed = steps_passed == total_steps
        details = f"passed={steps_passed}/{total_steps} steps"
        return _make_result(spec, passed, score, details)


@register_grader("cross_document_match")
class CrossDocumentMatch:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        source_field = spec.config.get("source_field", "")
        target_field = spec.config.get("target_field", "")
        case_sensitive = spec.config.get("case_sensitive", False)

        if source_field and target_field:
            source = _get_field(output, source_field)
            target = _get_field(expected, target_field)
        elif spec.field:
            source = _get_field(output, spec.field)
            target = _get_field(expected, spec.field)
        else:
            return _make_result(spec, False, 0.0, "No source_field/target_field or spec.field configured")

        if source is _MISSING:
            field_label = source_field or spec.field or ""
            return _make_result(spec, False, 0.0, f"Source field '{field_label}' not found in output")

        if target is _MISSING:
            field_label = target_field or spec.field or ""
            return _make_result(spec, False, 0.0, f"Target field '{field_label}' not found in expected")

        if isinstance(source, str) and isinstance(target, str) and not case_sensitive:
            passed = source.lower() == target.lower()
        else:
            passed = source == target

        score = 1.0 if passed else 0.0
        details = f"source={source!r} vs target={target!r}"
        return _make_result(spec, passed, score, details)


@register_grader("array_sum_match")
class ArraySumMatch:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        value_field = spec.config.get("value_field", "")
        total_field = spec.config.get("total_field", "")
        tolerance = float(spec.config.get("tolerance", 0.01))

        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        if not total_field:
            return _make_result(spec, False, 0.0, "No total_field configured")

        array = _get_field(output, field)
        if array is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{field}' not found in output")

        if not isinstance(array, list):
            return _make_result(spec, False, 0.0, f"Field '{field}' is not an array")

        expected_total = _get_field(expected, total_field)
        if expected_total is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{total_field}' not found in expected")

        try:
            total_val = float(expected_total)
        except (ValueError, TypeError):
            return _make_result(spec, False, 0.0, f"Non-numeric total: {expected_total!r}")

        array_sum = 0.0
        for item in array:
            raw = item.get(value_field) if value_field and isinstance(item, dict) else item
            try:
                array_sum += float(raw)  # type: ignore[arg-type]
            except (ValueError, TypeError):
                return _make_result(spec, False, 0.0, f"Non-numeric value in array: {raw!r}")

        max_diff = abs(total_val * tolerance) if total_val != 0 else tolerance
        diff = abs(array_sum - total_val)
        passed = diff <= max_diff
        score = max(0.0, 1.0 - (diff / max_diff)) if max_diff > 0 else (1.0 if diff == 0 else 0.0)
        details = f"sum={array_sum:.2f}, expected={total_val:.2f}, diff={diff:.4f}"
        return _make_result(spec, passed, score, details)


@register_grader("fuzzy_name_match")
class FuzzyNameMatch:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        field = spec.field
        threshold = float(spec.config.get("threshold", 0.85))
        normalize = spec.config.get("normalize", True)

        if not field:
            return _make_result(spec, False, 0.0, "No field specified")

        actual = _get_field(output, field)
        reference = _get_field(expected, field)

        if actual is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{field}' not found in output")

        if reference is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{field}' not found in expected")

        s1 = str(actual)
        s2 = str(reference)

        if normalize:
            s1 = _normalize_name(s1)
            s2 = _normalize_name(s2)

        sim = _jaro_winkler(s1, s2)
        passed = sim >= threshold
        score = sim
        details = f"similarity={sim:.3f}, threshold={threshold}"
        return _make_result(spec, passed, score, details)
