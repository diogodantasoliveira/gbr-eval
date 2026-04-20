"""Field-level F1 grader with fuzzy matching support."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from gbr_eval.graders.base import register_grader
from gbr_eval.graders.deterministic import _MISSING, _get_field
from gbr_eval.harness.models import GraderResult, GraderSpec


def _fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


def _numeric_match(a: Any, b: Any, tolerance: float = 0.01) -> bool:
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) <= abs(fb * tolerance) if fb != 0 else abs(fa - fb) <= tolerance
    except (ValueError, TypeError):
        return False


def _compare_list(actual: list[Any], expected: list[Any], fuzzy_ratio: float, numeric_tolerance: float) -> bool:
    if len(actual) != len(expected):
        return False
    matched_indices: set[int] = set()
    for exp_item in expected:
        found = False
        for i, act_item in enumerate(actual):
            if i not in matched_indices and _compare_field(act_item, exp_item, fuzzy_ratio, numeric_tolerance):
                matched_indices.add(i)
                found = True
                break
        if not found:
            return False
    return True


def _compare_field(actual: Any, expected: Any, fuzzy_ratio: float, numeric_tolerance: float) -> bool:
    if actual is None or expected is None:
        return bool(actual == expected)

    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual == expected

    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return _compare_list(actual, expected, fuzzy_ratio, numeric_tolerance)

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        if set(expected.keys()) != set(actual.keys()):
            return False
        return all(_compare_field(actual[k], expected[k], fuzzy_ratio, numeric_tolerance) for k in expected)

    if isinstance(expected, (int, float)):
        return _numeric_match(actual, expected, numeric_tolerance)

    return _fuzzy_match(str(actual), str(expected), fuzzy_ratio)


@register_grader("field_f1")
class FieldF1:
    """Compute F1 score over extracted fields, supporting fuzzy and numeric matching."""

    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        scope = spec.config.get("scope", "all")
        critical_fields: list[str] = spec.config.get("critical_fields", [])
        fuzzy_ratio = float(spec.config.get("fuzzy_ratio", 0.85))
        numeric_tolerance = float(spec.config.get("numeric_tolerance", 0.01))

        if spec.field:
            fields_to_check = [spec.field]
        elif scope == "critical_only" and critical_fields:
            fields_to_check = critical_fields
        else:
            fields_to_check = list(expected.keys())

        if scope == "critical_only" and not critical_fields and not spec.field:
            return GraderResult(
                grader_type="field_f1",
                field=spec.field,
                passed=False,
                score=0.0,
                weight=spec.weight,
                required=spec.required,
                details="scope=critical_only but no critical_fields configured",
            )

        if not fields_to_check:
            return GraderResult(
                grader_type="field_f1",
                field=spec.field,
                passed=True,
                score=1.0,
                weight=spec.weight,
                required=spec.required,
                details="No fields to check",
            )

        true_positives = 0
        false_positives = 0
        false_negatives = 0

        for field_name in fields_to_check:
            exp_val = _get_field(expected, field_name)
            act_val = _get_field(output, field_name)

            if act_val is _MISSING and exp_val is _MISSING:
                continue
            if act_val is _MISSING:
                false_negatives += 1
            elif exp_val is _MISSING:
                false_positives += 1
            elif exp_val is None and act_val is None:
                true_positives += 1
            elif exp_val is not None and act_val is not None:
                if _compare_field(act_val, exp_val, fuzzy_ratio, numeric_tolerance):
                    true_positives += 1
                else:
                    false_positives += 1
                    false_negatives += 1
            elif exp_val is not None:
                false_negatives += 1
            else:
                false_positives += 1

        tp_fp = true_positives + false_positives
        tp_fn = true_positives + false_negatives
        precision = true_positives / tp_fp if tp_fp > 0 else 0.0
        recall = true_positives / tp_fn if tp_fn > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        threshold = float(spec.config.get("f1_threshold", 0.90))
        passed = f1 >= threshold

        details = (
            f"F1={f1:.3f} (P={precision:.3f}, R={recall:.3f}), "
            f"TP={true_positives}, FP={false_positives}, FN={false_negatives}, "
            f"threshold={threshold}"
        )

        return GraderResult(
            grader_type="field_f1",
            field=spec.field,
            passed=passed,
            score=f1,
            weight=spec.weight,
            required=spec.required,
            details=details,
        )
