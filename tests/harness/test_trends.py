"""Tests for trend detection across eval runs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from gbr_eval.harness.models import EvalRun, GraderResult, Layer, TaskResult, Tier
from gbr_eval.harness.trends import _linear_slope, detect_trends, load_runs_from_dir


def _make_grader_result(passed: bool = True, score: float = 1.0) -> GraderResult:
    return GraderResult(grader_type="exact_match", passed=passed, score=score)


def _make_task_result(task_id: str, score: float = 1.0, pass_threshold: float = 0.95) -> TaskResult:
    return TaskResult(
        task_id=task_id,
        passed=score >= pass_threshold,
        score=score,
        pass_threshold=pass_threshold,
        grader_results=[_make_grader_result(passed=score >= pass_threshold, score=score)],
    )


def _make_run(run_id: str, started_at: datetime, task_results: list[TaskResult]) -> EvalRun:
    return EvalRun(
        run_id=run_id,
        layer=Layer.PRODUCT,
        tier=Tier.GATE,
        started_at=started_at,
        task_results=task_results,
        tasks_total=len(task_results),
    )


class TestDetectTrends:
    def test_no_trend_stable_scores(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=0.9)])
            for i in range(5)
        ]

        alerts = detect_trends(runs)

        assert alerts == []

    def test_declining_detected(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [1.0, 0.9, 0.8, 0.7, 0.6]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=s)])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3)

        assert len(alerts) == 1
        assert alerts[0].task_id == "task.A"
        assert alerts[0].direction == "declining"
        assert alerts[0].consecutive_runs == 3

    def test_improving_detected(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [0.5, 0.6, 0.7, 0.8, 0.9]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=s)])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3)

        assert len(alerts) == 1
        assert alerts[0].direction == "improving"

    def test_insufficient_runs_returns_empty(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        runs = [
            _make_run("run-0", base, [_make_task_result("task.A", score=1.0)]),
            _make_run("run-1", base + timedelta(days=1), [_make_task_result("task.A", score=0.5)]),
        ]

        alerts = detect_trends(runs, min_consecutive=3)

        assert alerts == []

    def test_approaching_threshold_distance(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [0.99, 0.97, 0.96]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=s)])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3)

        assert len(alerts) == 1
        assert alerts[0].distance_to_threshold == pytest.approx(0.96 - 0.95)
        assert alerts[0].threshold == 0.95

    def test_mixed_tasks_independent(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [
                _make_task_result("task.A", score=1.0 - i * 0.1),
                _make_task_result("task.B", score=0.8),
            ])
            for i in range(4)
        ]

        alerts = detect_trends(runs, min_consecutive=3)

        declining = [a for a in alerts if a.task_id == "task.A"]
        stable = [a for a in alerts if a.task_id == "task.B"]
        assert len(declining) == 1
        assert declining[0].direction == "declining"
        assert stable == []


class TestLoadRunsFromDir:
    def test_loads_all_json_files(self, tmp_path):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        for i in range(3):
            run = _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A")])
            (tmp_path / f"run_{i}.json").write_text(run.model_dump_json())

        runs = load_runs_from_dir(tmp_path)

        assert len(runs) == 3
        assert {r.run_id for r in runs} == {"run-0", "run-1", "run-2"}

    def test_empty_dir_returns_empty(self, tmp_path):
        runs = load_runs_from_dir(tmp_path)

        assert runs == []

    def test_ignores_non_json_files(self, tmp_path):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        run = _make_run("run-0", base, [_make_task_result("task.A")])
        (tmp_path / "run_0.json").write_text(run.model_dump_json())
        (tmp_path / "notes.txt").write_text("not a run")

        runs = load_runs_from_dir(tmp_path)

        assert len(runs) == 1


class TestTrendsUsesTaskThreshold:
    def test_threshold_from_task_result(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [0.99, 0.97, 0.96]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [
                _make_task_result("task.A", score=s, pass_threshold=0.90),
            ])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3)

        assert len(alerts) == 1
        assert alerts[0].threshold == 0.90
        assert alerts[0].distance_to_threshold == pytest.approx(0.96 - 0.90)


class TestLinearSlope:
    """M fix: least-squares slope helper for trend detection."""

    def test_constant_slope_zero(self):
        assert _linear_slope([1.0, 1.0, 1.0, 1.0]) == pytest.approx(0.0)

    def test_perfect_decline(self):
        assert _linear_slope([1.0, 0.9, 0.8, 0.7]) == pytest.approx(-0.1)

    def test_perfect_increase(self):
        assert _linear_slope([0.7, 0.8, 0.9, 1.0]) == pytest.approx(0.1)

    def test_single_value_returns_zero(self):
        assert _linear_slope([0.5]) == 0.0

    def test_empty_returns_zero(self):
        assert _linear_slope([]) == 0.0

    def test_noisy_decline(self):
        slope = _linear_slope([0.98, 0.96, 0.97, 0.94, 0.93])
        assert slope < 0


class TestSlopeBasedTrends:
    """M fix: slope-based detection catches noisy degradation."""

    def test_noisy_decline_detected_by_slope(self):
        """Noisy decline where last 3 are NOT monotonic but slope is negative."""
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [0.98, 0.94, 0.96, 0.92, 0.93]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=s)])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3, slope_window=5, slope_threshold=-0.01)

        slope_alerts = [a for a in alerts if a.direction == "declining_trend"]
        assert len(slope_alerts) == 1
        assert slope_alerts[0].task_id == "task.A"

    def test_stable_scores_no_slope_alert(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [0.95, 0.96, 0.95, 0.96, 0.95]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=s)])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3, slope_window=5, slope_threshold=-0.02)

        slope_alerts = [a for a in alerts if a.direction == "declining_trend"]
        assert slope_alerts == []

    def test_monotonic_decline_not_duplicated_as_slope(self):
        """When monotonic detection fires, slope should NOT also fire."""
        base = datetime(2026, 1, 1, tzinfo=UTC)
        scores = [1.0, 0.9, 0.8, 0.7, 0.6]
        runs = [
            _make_run(f"run-{i}", base + timedelta(days=i), [_make_task_result("task.A", score=s)])
            for i, s in enumerate(scores)
        ]

        alerts = detect_trends(runs, min_consecutive=3, slope_window=5, slope_threshold=-0.01)

        directions = [a.direction for a in alerts if a.task_id == "task.A"]
        assert "declining" in directions
        assert "declining_trend" not in directions
