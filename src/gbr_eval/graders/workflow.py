"""Workflow and aggregate graders for Caixa BPO eval."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gbr_eval.graders._shared import _make_result
from gbr_eval.graders.base import register_grader

if TYPE_CHECKING:
    from gbr_eval.harness.models import GraderResult, GraderSpec

_MISSING = object()


def _get_field(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        if isinstance(current, dict):
            if key not in current:
                return _MISSING
            current = current[key]
        else:
            return _MISSING
    return current


@register_grader("workflow_steps")
class WorkflowSteps:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        steps_field = spec.config.get("steps_field", "etapas_executadas")
        expected_steps_field = spec.config.get("expected_steps_field", "etapas_esperadas")

        actual_steps = _get_field(output, steps_field)
        if actual_steps is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{steps_field}' not found in output")

        if not isinstance(actual_steps, list):
            return _make_result(spec, False, 0.0, f"Field '{steps_field}' is not a list")

        expected_steps = _get_field(expected, expected_steps_field)
        if expected_steps is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{expected_steps_field}' not found in expected")

        if not isinstance(expected_steps, list):
            return _make_result(spec, False, 0.0, f"Field '{expected_steps_field}' is not a list")

        if not expected_steps:
            return _make_result(spec, True, 1.0, "steps=0/0, order_correct=True")

        # Build index map for actual steps (first occurrence of each step)
        actual_index: dict[Any, int] = {}
        for i, step in enumerate(actual_steps):
            if step not in actual_index:
                actual_index[step] = i

        # Count steps present and check consecutive ordering
        present_in_order = 0
        order_correct = True
        prev_index: int | None = None

        for step in expected_steps:
            if step in actual_index:
                idx = actual_index[step]
                if prev_index is not None and idx <= prev_index:
                    order_correct = False
                present_in_order += 1
                prev_index = idx
            else:
                order_correct = False

        total_expected = len(expected_steps)
        actual_count = len(actual_steps)
        score = present_in_order / total_expected
        passed = score >= 1.0 and order_correct
        details = f"steps={actual_count}/{total_expected}, order_correct={order_correct}"
        return _make_result(spec, passed, score, details)


@register_grader("classification_accuracy")
class ClassificationAccuracy:
    def grade(self, output: dict[str, Any], expected: dict[str, Any], spec: GraderSpec) -> GraderResult:
        predictions_field = spec.config.get("predictions_field", "predictions")
        threshold = float(spec.config.get("threshold", 0.90))

        predictions = _get_field(output, predictions_field)
        if predictions is _MISSING:
            return _make_result(spec, False, 0.0, f"Field '{predictions_field}' not found in output")

        if not isinstance(predictions, list):
            return _make_result(spec, False, 0.0, f"Field '{predictions_field}' is not a list")

        total = len(predictions)
        if total == 0:
            return _make_result(spec, False, 0.0, "Empty predictions array")

        correct = 0
        for item in predictions:
            if not isinstance(item, dict):
                continue
            predicted = item.get("predicted")
            actual = item.get("actual")
            if predicted is None or actual is None:
                continue
            if str(predicted).lower() == str(actual).lower():
                correct += 1

        accuracy = correct / total
        passed = accuracy >= threshold
        details = f"accuracy={accuracy:.3f} ({correct}/{total}), threshold={threshold}"
        return _make_result(spec, passed, accuracy, details)
