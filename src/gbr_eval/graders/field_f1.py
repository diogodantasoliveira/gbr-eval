"""Field-level F1 grader with fuzzy matching support."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from gbr_eval.graders.base import register_grader
from gbr_eval.harness.models import GraderResult, GraderSpec


def _fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


def _numeric_match(a: Any, b: Any, tolerance: float = 0.01) -> bool:
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) <= abs(fb * tolerance) if fb != 0 else abs(fa - fb) <= tolerance
    except (ValueError, TypeError):
        return False


def _compare_field(actual: Any, expected: Any, fuzzy_ratio: float, numeric_tolerance: float) -> bool:
    if actual is None or expected is None:
        return actual == expected

    if isinstance(expected, bool):
        return actual == expected

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

        if scope == "critical_only" and critical_fields:
            fields_to_check = critical_fields
        else:
            fields_to_check = list(expected.keys())

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
            exp_val = expected.get(field_name)
            act_val = output.get(field_name)

            if exp_val is not None and act_val is not None:
                if _compare_field(act_val, exp_val, fuzzy_ratio, numeric_tolerance):
                    true_positives += 1
                else:
                    false_positives += 1
                    false_negatives += 1
            elif exp_val is not None and act_val is None:
                false_negatives += 1
            elif exp_val is None and act_val is not None:
                false_positives += 1

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
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
