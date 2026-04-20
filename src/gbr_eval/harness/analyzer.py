"""Analyze eval runs — find weak fields, skills, and error patterns."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gbr_eval.harness.models import EvalRun


@dataclass
class TaskStats:
    task_id: str
    run_count: int = 0
    pass_count: int = 0
    scores: list[float] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.pass_count / self.run_count if self.run_count else 0.0

    @property
    def avg_score(self) -> float:
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def min_score(self) -> float:
        return min(self.scores) if self.scores else 0.0

    @property
    def p5_score(self) -> float:
        if not self.scores:
            return 0.0
        s = sorted(self.scores)
        if len(s) < 20:
            return s[0]  # too few samples for meaningful p5
        idx = max(0, int(len(s) * 0.05) - 1)
        return s[idx]


@dataclass
class FieldStats:
    field_name: str
    grader_type: str
    total: int = 0
    passed: int = 0
    failed: int = 0

    @property
    def fail_rate(self) -> float:
        return self.failed / self.total if self.total else 0.0


@dataclass
class AnalysisReport:
    runs_analyzed: int
    task_stats: list[TaskStats]
    field_stats: list[FieldStats]
    weakest_tasks: list[TaskStats]
    most_failing_fields: list[FieldStats]


def analyze_runs(runs: list[EvalRun], top_n: int = 10) -> AnalysisReport:
    task_map: dict[str, TaskStats] = {}
    field_map: dict[str, FieldStats] = defaultdict(lambda: FieldStats(field_name="", grader_type=""))

    for run in runs:
        for result in run.task_results:
            if result.task_id not in task_map:
                task_map[result.task_id] = TaskStats(task_id=result.task_id)
            ts = task_map[result.task_id]
            ts.run_count += 1
            ts.scores.append(result.score)
            if result.passed:
                ts.pass_count += 1

            for gr in result.grader_results:
                field_name = gr.field or gr.grader_type
                key = f"{result.task_id}:{field_name}"
                if key not in field_map:
                    field_map[key] = FieldStats(field_name=field_name, grader_type=gr.grader_type)
                fs = field_map[key]
                fs.total += 1
                if gr.passed:
                    fs.passed += 1
                else:
                    fs.failed += 1

    all_tasks = sorted(task_map.values(), key=lambda t: t.avg_score)
    all_fields = sorted(field_map.values(), key=lambda f: f.fail_rate, reverse=True)

    weakest = [t for t in all_tasks if t.pass_rate < 1.0][:top_n]
    failing = [f for f in all_fields if f.failed > 0][:top_n]

    return AnalysisReport(
        runs_analyzed=len(runs),
        task_stats=all_tasks,
        field_stats=list(field_map.values()),
        weakest_tasks=weakest,
        most_failing_fields=failing,
    )


def format_analysis(report: AnalysisReport) -> str:
    lines: list[str] = []
    lines.append(f"Eval Analysis — {report.runs_analyzed} runs analyzed")
    lines.append("=" * 60)

    lines.append(f"\nTask Summary ({len(report.task_stats)} tasks):")
    for ts in report.task_stats:
        symbol = "PASS" if ts.pass_rate == 1.0 else "WARN" if ts.pass_rate >= 0.8 else "FAIL"
        lines.append(
            f"  [{symbol}] {ts.task_id}: "
            f"pass_rate={ts.pass_rate:.0%}, avg={ts.avg_score:.3f}, "
            f"min={ts.min_score:.3f}, runs={ts.run_count}"
        )

    if report.weakest_tasks:
        lines.append("\nWeakest Tasks (pass_rate < 100%):")
        for ts in report.weakest_tasks:
            lines.append(f"  {ts.task_id}: pass_rate={ts.pass_rate:.0%}, avg={ts.avg_score:.3f}")

    if report.most_failing_fields:
        lines.append("\nMost Failing Fields:")
        for fs in report.most_failing_fields:
            lines.append(
                f"  {fs.field_name} ({fs.grader_type}): "
                f"{fs.failed}/{fs.total} failed ({fs.fail_rate:.0%})"
            )

    return "\n".join(lines)


def analysis_to_dict(report: AnalysisReport) -> dict[str, Any]:
    return {
        "runs_analyzed": report.runs_analyzed,
        "task_stats": [
            {
                "task_id": ts.task_id,
                "run_count": ts.run_count,
                "pass_rate": ts.pass_rate,
                "avg_score": ts.avg_score,
                "min_score": ts.min_score,
                "p5_score": ts.p5_score,
            }
            for ts in report.task_stats
        ],
        "weakest_tasks": [
            {"task_id": ts.task_id, "pass_rate": ts.pass_rate, "avg_score": ts.avg_score}
            for ts in report.weakest_tasks
        ],
        "most_failing_fields": [
            {
                "field_name": fs.field_name,
                "grader_type": fs.grader_type,
                "failed": fs.failed,
                "total": fs.total,
                "fail_rate": fs.fail_rate,
            }
            for fs in report.most_failing_fields
        ],
    }
