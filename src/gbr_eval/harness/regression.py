"""Regression delta analysis and gate classification for eval runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from gbr_eval.harness.models import EvalRun, GateResult

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class RegressionDelta:
    baseline_run_id: str
    current_run_id: str
    newly_failing: list[str] = field(default_factory=list)
    newly_passing: list[str] = field(default_factory=list)
    new_tasks: list[str] = field(default_factory=list)
    removed_tasks: list[str] = field(default_factory=list)
    score_deltas: dict[str, float] = field(default_factory=dict)
    degraded_scores: list[str] = field(default_factory=list)
    stable_pass: list[str] = field(default_factory=list)
    stable_fail: list[str] = field(default_factory=list)
    overall_delta: float = 0.0
    has_regressions: bool = False


def compare_runs(
    baseline: EvalRun,
    current: EvalRun,
    score_degradation_threshold: float = 0.05,
) -> RegressionDelta:
    baseline_map = {tr.task_id: tr for tr in baseline.task_results}
    current_map = {tr.task_id: tr for tr in current.task_results}

    common_ids = baseline_map.keys() & current_map.keys()
    new_tasks = [tid for tid in current_map if tid not in baseline_map]
    removed_tasks = [tid for tid in baseline_map if tid not in current_map]

    newly_failing: list[str] = []
    newly_passing: list[str] = []
    stable_pass: list[str] = []
    stable_fail: list[str] = []
    score_deltas: dict[str, float] = {}
    degraded_scores: list[str] = []

    for task_id in common_ids:
        baseline_result = baseline_map[task_id]
        current_result = current_map[task_id]

        if baseline_result.passed and not current_result.passed:
            newly_failing.append(task_id)
        elif not baseline_result.passed and current_result.passed:
            newly_passing.append(task_id)
        elif baseline_result.passed and current_result.passed:
            stable_pass.append(task_id)
        else:
            stable_fail.append(task_id)

        score_deltas[task_id] = current_result.score - baseline_result.score

        # Detect significant score degradation within passing tasks
        if (baseline_result.passed and current_result.passed
                and score_deltas[task_id] < -score_degradation_threshold):
            degraded_scores.append(task_id)

    return RegressionDelta(
        baseline_run_id=baseline.run_id,
        current_run_id=current.run_id,
        newly_failing=newly_failing,
        newly_passing=newly_passing,
        new_tasks=new_tasks,
        removed_tasks=removed_tasks,
        score_deltas=score_deltas,
        degraded_scores=degraded_scores,
        stable_pass=stable_pass,
        stable_fail=stable_fail,
        overall_delta=current.overall_score - baseline.overall_score,
        has_regressions=len(newly_failing) > 0 or len(degraded_scores) > 0,
    )


def load_baseline(path: Path) -> EvalRun:
    return EvalRun.model_validate_json(path.read_text())


def classify_gate(
    run: EvalRun,
    delta: RegressionDelta | None = None,
) -> GateResult:
    """Classify gate outcome from individual grader results, not from overall_score.

    overall_score is a pass-rate (tasks_passed/tasks_total) and does not reflect
    whether required graders passed. Gate classification must inspect grader-level
    results to correctly distinguish NO_GO from CONDITIONAL_GO.
    """
    if delta is not None and delta.has_regressions:
        return GateResult.NO_GO_ABSOLUTE

    all_grader_results = [gr for tr in run.task_results for gr in tr.grader_results]
    if any(gr.required and not gr.passed for gr in all_grader_results):
        return GateResult.NO_GO

    all_passed = all(tr.passed for tr in run.task_results)
    all_optional_passed = all(
        gr.passed for gr in all_grader_results if not gr.required
    )

    if all_passed and all_optional_passed:
        return GateResult.GO

    return GateResult.CONDITIONAL_GO
