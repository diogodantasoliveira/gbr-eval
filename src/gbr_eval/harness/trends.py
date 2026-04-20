"""Trend detection across multiple eval runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003

from gbr_eval.harness.models import EvalRun


@dataclass
class TrendAlert:
    task_id: str
    metric: str          # "score" | "duration_ms"
    direction: str       # "declining" | "improving"
    consecutive_runs: int
    current_value: float
    threshold: float
    distance_to_threshold: float


def _linear_slope(values: list[float]) -> float:
    """Compute least-squares slope of values indexed 0..n-1. No external deps."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    return numerator / denominator if denominator != 0 else 0.0


def detect_trends(
    runs: list[EvalRun],
    min_consecutive: int = 3,
    slope_window: int = 5,
    slope_threshold: float = -0.02,
) -> list[TrendAlert]:
    """Analyze chronologically-ordered runs for score degradation trends."""
    if len(runs) < min_consecutive:
        return []

    sorted_runs = sorted(runs, key=lambda r: r.started_at)

    # Collect all task_ids that appear in every run
    all_task_ids: set[str] = set()
    for run in sorted_runs:
        for tr in run.task_results:
            all_task_ids.add(tr.task_id)

    alerts: list[TrendAlert] = []

    for task_id in sorted(all_task_ids):
        # Get scores for this task across runs (only runs where task exists)
        scores: list[float] = []
        threshold = 0.95
        for run in sorted_runs:
            for tr in run.task_results:
                if tr.task_id == task_id:
                    scores.append(tr.score)
                    threshold = tr.pass_threshold
                    break

        if len(scores) < min_consecutive:
            continue

        # Check last min_consecutive scores for strictly declining trend
        tail = scores[-min_consecutive:]
        is_declining = all(tail[i] > tail[i + 1] for i in range(len(tail) - 1))
        is_improving = all(tail[i] < tail[i + 1] for i in range(len(tail) - 1))

        current_value = scores[-1]
        distance = current_value - threshold

        if is_declining:
            alerts.append(TrendAlert(
                task_id=task_id,
                metric="score",
                direction="declining",
                consecutive_runs=min_consecutive,
                current_value=current_value,
                threshold=threshold,
                distance_to_threshold=distance,
            ))
        elif is_improving:
            alerts.append(TrendAlert(
                task_id=task_id,
                metric="score",
                direction="improving",
                consecutive_runs=min_consecutive,
                current_value=current_value,
                threshold=threshold,
                distance_to_threshold=distance,
            ))

        # Slope-based detection over a wider window
        if len(scores) >= slope_window:
            window = scores[-slope_window:]
            slope = _linear_slope(window)
            if slope <= slope_threshold and not is_declining:
                alerts.append(TrendAlert(
                    task_id=task_id,
                    metric="score",
                    direction="declining_trend",
                    consecutive_runs=slope_window,
                    current_value=current_value,
                    threshold=threshold,
                    distance_to_threshold=distance,
                ))

    return alerts


def load_runs_from_dir(runs_dir: Path) -> list[EvalRun]:
    """Load all JSON run files from a directory."""
    runs: list[EvalRun] = []
    for json_file in sorted(runs_dir.glob("*.json")):
        runs.append(EvalRun.model_validate_json(json_file.read_text()))
    return runs
