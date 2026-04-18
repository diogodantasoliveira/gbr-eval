"""Report generation for eval runs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from gbr_eval.harness.models import EvalRun


def console_report(run: EvalRun) -> str:
    lines = [
        f"{'='*60}",
        f"  Eval Run: {run.run_id[:8]}",
        f"  Layer: {run.layer.value}  |  Tier: {run.tier.value if run.tier else 'all'}",
        f"  Started: {run.started_at.isoformat()}",
        f"{'='*60}",
        "",
    ]

    for result in run.task_results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"  [{status}] {result.task_id}  score={result.score:.3f}  ({result.duration_ms:.0f}ms)")

        for gr in result.grader_results:
            g_status = "ok" if gr.passed else "FAIL"
            field_str = f" [{gr.field}]" if gr.field else ""
            lines.append(f"         {g_status} {gr.grader_type}{field_str}: {gr.details}")
            if gr.error:
                lines.append(f"         ERROR: {gr.error}")

        lines.append("")

    lines.extend([
        f"{'='*60}",
        f"  Total: {run.tasks_total}  |  Pass: {run.tasks_passed}  |  Fail: {run.tasks_failed}",
        f"  Overall: {run.overall_score:.1%}",
        f"{'='*60}",
    ])

    return "\n".join(lines)


def json_report(run: EvalRun, output_path: Path | None = None) -> str:
    data = run.model_dump(mode="json")
    report = json.dumps(data, indent=2, ensure_ascii=False, default=str)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)

    return report


def ci_summary(run: EvalRun) -> str:
    """One-line summary for CI output."""
    status = "PASSED" if run.tasks_failed == 0 else "FAILED"
    failed_tasks = [r.task_id for r in run.task_results if not r.passed]
    summary = f"gbr-eval {status}: {run.tasks_passed}/{run.tasks_total} tasks passed ({run.overall_score:.1%})"
    if failed_tasks:
        summary += f" | Failed: {', '.join(failed_tasks)}"
    return summary


def failed_details(run: EvalRun) -> list[dict[str, object]]:
    """Extract details of failed tasks for CI annotations."""
    failures: list[dict[str, object]] = []
    for result in run.task_results:
        if result.passed:
            continue
        failed_graders = [
            {"type": gr.grader_type, "field": gr.field, "details": gr.details, "error": gr.error}
            for gr in result.grader_results
            if not gr.passed
        ]
        failures.append({
            "task_id": result.task_id,
            "score": result.score,
            "failed_graders": failed_graders,
        })
    return failures
