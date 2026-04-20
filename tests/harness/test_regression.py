"""Tests for regression delta and gate classification."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.harness.models import EvalRun, GateResult, GraderResult, Layer, TaskResult, Tier
from gbr_eval.harness.regression import RegressionDelta, classify_gate, compare_runs, load_baseline


def _make_grader_result(
    grader_type: str = "exact_match",
    passed: bool = True,
    score: float = 1.0,
    required: bool = False,
) -> GraderResult:
    return GraderResult(
        grader_type=grader_type,
        passed=passed,
        score=score,
        required=required,
    )


def _make_task_result(
    task_id: str,
    passed: bool = True,
    score: float = 1.0,
    grader_results: list[GraderResult] | None = None,
) -> TaskResult:
    return TaskResult(
        task_id=task_id,
        passed=passed,
        score=score,
        grader_results=grader_results or [_make_grader_result(passed=passed, score=score)],
    )


def _make_eval_run(
    run_id: str,
    task_results: list[TaskResult],
    overall_score: float = 1.0,
) -> EvalRun:
    return EvalRun(
        run_id=run_id,
        layer=Layer.PRODUCT,
        tier=Tier.GATE,
        task_results=task_results,
        overall_score=overall_score,
    )


class TestCompareRuns:
    def test_identical_runs_no_regressions(self):
        tr = _make_task_result("task.A", passed=True, score=1.0)
        baseline = _make_eval_run("run-1", [tr])
        current = _make_eval_run("run-2", [tr])

        delta = compare_runs(baseline, current)

        assert delta.newly_failing == []
        assert delta.newly_passing == []
        assert not delta.has_regressions

    def test_newly_failing_detected(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=True)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=False, score=0.0)])

        delta = compare_runs(baseline, current)

        assert "task.A" in delta.newly_failing
        assert delta.has_regressions is True

    def test_newly_passing_detected(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=False, score=0.0)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=True)])

        delta = compare_runs(baseline, current)

        assert "task.A" in delta.newly_passing
        assert delta.has_regressions is False

    def test_score_deltas_computed(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", score=0.8)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", score=1.0)])

        delta = compare_runs(baseline, current)

        assert delta.score_deltas["task.A"] == pytest.approx(0.2)

    def test_new_task_not_regression(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A")])
        current = _make_eval_run("run-2", [_make_task_result("task.A"), _make_task_result("task.B")])

        delta = compare_runs(baseline, current)

        assert "task.B" in delta.new_tasks
        assert "task.B" not in delta.newly_passing
        assert not delta.has_regressions

    def test_removed_task_not_regression(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A"), _make_task_result("task.C")])
        current = _make_eval_run("run-2", [_make_task_result("task.A")])

        delta = compare_runs(baseline, current)

        assert "task.C" in delta.removed_tasks
        assert "task.C" not in delta.newly_failing
        assert not delta.has_regressions

    def test_has_regressions_true_when_newly_failing(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=True)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=False, score=0.0)])

        delta = compare_runs(baseline, current)

        assert delta.has_regressions is True

    def test_overall_delta_computed(self):
        baseline = _make_eval_run("run-1", [], overall_score=0.5)
        current = _make_eval_run("run-2", [], overall_score=1.0)

        delta = compare_runs(baseline, current)

        assert delta.overall_delta == pytest.approx(0.5)

    def test_renamed_task_not_false_regression(self):
        baseline = _make_eval_run("run-1", [_make_task_result("old_name", passed=True)])
        current = _make_eval_run("run-2", [_make_task_result("new_name", passed=True)])

        delta = compare_runs(baseline, current)

        assert "new_name" in delta.new_tasks
        assert "old_name" in delta.removed_tasks
        assert delta.newly_failing == []
        assert delta.newly_passing == []


class TestClassifyGate:
    def test_go_when_all_pass(self):
        tr = _make_task_result(
            "task.A",
            passed=True,
            score=1.0,
            grader_results=[_make_grader_result(passed=True, required=True)],
        )
        run = _make_eval_run("run-1", [tr])

        result = classify_gate(run)

        assert result == GateResult.GO

    def test_conditional_go_optional_fail(self):
        grader_required = _make_grader_result(passed=True, required=True)
        grader_optional = _make_grader_result(grader_type="field_f1", passed=False, score=0.5, required=False)
        tr = _make_task_result(
            "task.A",
            passed=False,
            score=0.5,
            grader_results=[grader_required, grader_optional],
        )
        run = _make_eval_run("run-1", [tr])

        result = classify_gate(run)

        assert result == GateResult.CONDITIONAL_GO

    def test_no_go_required_fail(self):
        grader = _make_grader_result(passed=False, score=0.0, required=True)
        tr = _make_task_result("task.A", passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run("run-1", [tr])

        result = classify_gate(run)

        assert result == GateResult.NO_GO

    def test_no_go_absolute_regression(self):
        tr = _make_task_result("task.A", passed=True)
        run = _make_eval_run("run-2", [tr])
        delta = RegressionDelta(
            baseline_run_id="run-1",
            current_run_id="run-2",
            newly_failing=["task.A"],
            has_regressions=True,
        )

        result = classify_gate(run, delta=delta)

        assert result == GateResult.NO_GO_ABSOLUTE

    def test_go_without_delta(self):
        grader = _make_grader_result(passed=True, required=True)
        tr = _make_task_result("task.A", passed=True, grader_results=[grader])
        run = _make_eval_run("run-1", [tr])

        result = classify_gate(run, delta=None)

        assert result == GateResult.GO

    def test_conditional_go_task_fails_but_no_required_failures(self):
        grader = _make_grader_result(passed=False, score=0.4, required=False)
        tr = _make_task_result("task.A", passed=False, score=0.4, grader_results=[grader])
        run = _make_eval_run("run-1", [tr])

        result = classify_gate(run)

        assert result == GateResult.CONDITIONAL_GO


class TestLoadBaseline:
    def test_loads_valid_json(self, tmp_path: Path):
        run = _make_eval_run("run-baseline", [_make_task_result("task.A")])
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(run.model_dump_json())

        loaded = load_baseline(baseline_file)

        assert loaded.run_id == "run-baseline"
        assert len(loaded.task_results) == 1
        assert loaded.task_results[0].task_id == "task.A"

    def test_invalid_json_raises(self, tmp_path: Path):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text('{"not_a_valid_eval_run": true}')

        with pytest.raises(ValidationError):
            load_baseline(baseline_file)


class TestDegradedScores:
    """M fix: detect significant score drops within passing tasks."""

    def test_score_degradation_detected(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=True, score=1.0)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=True, score=0.90)])

        delta = compare_runs(baseline, current, score_degradation_threshold=0.05)

        assert "task.A" in delta.degraded_scores
        assert delta.has_regressions is True

    def test_small_drop_not_flagged(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=True, score=1.0)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=True, score=0.97)])

        delta = compare_runs(baseline, current, score_degradation_threshold=0.05)

        assert delta.degraded_scores == []
        assert delta.has_regressions is False

    def test_degradation_only_in_passing_tasks(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=False, score=0.5)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=False, score=0.3)])

        delta = compare_runs(baseline, current, score_degradation_threshold=0.05)

        assert delta.degraded_scores == []

    def test_custom_threshold(self):
        baseline = _make_eval_run("run-1", [_make_task_result("task.A", passed=True, score=1.0)])
        current = _make_eval_run("run-2", [_make_task_result("task.A", passed=True, score=0.88)])

        delta = compare_runs(baseline, current, score_degradation_threshold=0.15)

        assert delta.degraded_scores == []

        delta2 = compare_runs(baseline, current, score_degradation_threshold=0.10)

        assert "task.A" in delta2.degraded_scores
