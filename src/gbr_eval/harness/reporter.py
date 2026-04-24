"""Report generation for eval runs."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement, tostring

from gbr_eval.harness.models import Severity

if TYPE_CHECKING:
    from pathlib import Path

    from gbr_eval.harness.models import EvalRun
    from gbr_eval.harness.regression import RegressionDelta


def console_report(run: EvalRun, delta: RegressionDelta | None = None) -> str:
    # Build header — include gate result when present
    project_line = f"  Project: {run.project}\n" if run.project != "default" else ""
    if run.gate_result is not None:
        gate_label = run.gate_result.value.upper().replace("_", " ")
        header_tier = run.tier.value if run.tier else "all"
        lines = [
            f"{'='*60}",
            f"  Eval Run: {run.run_id[:8]}",
        ]
        if project_line:
            lines.append(project_line.rstrip())
        lines.extend([
            f"  Layer: {run.layer.value}  |  Tier: {header_tier}  |  Gate: {gate_label}",
            f"  Started: {run.started_at.isoformat()}",
            f"{'='*60}",
            "",
        ])
    else:
        lines = [
            f"{'='*60}",
            f"  Eval Run: {run.run_id[:8]}",
        ]
        if project_line:
            lines.append(project_line.rstrip())
        lines.extend([
            f"  Layer: {run.layer.value}  |  Tier: {run.tier.value if run.tier else 'all'}",
            f"  Started: {run.started_at.isoformat()}",
            f"{'='*60}",
            "",
        ])

    for result in run.task_results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"  [{status}] {result.task_id}  score={result.score:.3f}  ({result.duration_ms:.0f}ms)")

        for gr in result.grader_results:
            g_status = "ok" if gr.passed else "FAIL"
            field_str = f" [{gr.field}]" if gr.field else ""
            lines.append(f"         {g_status} {gr.grader_type}{field_str}: {gr.details}")
            if gr.error:
                lines.append(f"         ERROR: {gr.error}")

        if result.reducer_scores and len(result.reducer_scores) > 1:
            reducer_str = ", ".join(f"{k}={v:.3f}" for k, v in result.reducer_scores.items())
            lines.append(f"         reducers: {reducer_str}")

        lines.append("")

    # Severity grouping — only shown when at least one grader has severity set
    failed_by_severity: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for result in run.task_results:
        for gr in result.grader_results:
            if not gr.passed and gr.severity is not None:
                field_str = f"[{gr.field}] " if gr.field else ""
                entry = (result.task_id, f"{field_str}{gr.grader_type}", gr.details)
                failed_by_severity[gr.severity.value.upper()].append(entry)

    if failed_by_severity:
        lines.append("  \u2500\u2500 Failures by Severity \u2500\u2500")
        severity_order = [s.value.upper() for s in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW)]
        for sev in severity_order:
            if sev not in failed_by_severity:
                continue
            entries = failed_by_severity[sev]
            lines.append(f"  {sev} ({len(entries)}):")
            for task_id, grader_label, details in entries:
                lines.append(f"    \u2717 [{task_id}] {grader_label}: {details}")
        lines.append("")

    # Regression delta section — only shown when baseline_run_id is set and delta is provided
    if run.baseline_run_id and delta is not None:
        lines.append(f"  \u2500\u2500 Regression Delta (vs {run.baseline_run_id[:6]}) \u2500\u2500")
        if delta.has_regressions:
            lines.append("  \u2717 REGRESSIONS DETECTED")
            for task_id in delta.newly_failing:
                score_delta = delta.score_deltas.get(task_id, 0.0)
                lines.append(f"  \u2193 Newly failing: {task_id} ({score_delta:+.1f})")
        else:
            lines.append("  \u2713 No regressions detected")
        for task_id in delta.newly_passing:
            score_delta = delta.score_deltas.get(task_id, 0.0)
            lines.append(f"  \u2191 Newly passing: {task_id} ({score_delta:+.1f})")
        lines.append("")

    # Funnel stats — only shown when funnel was active
    funnel = run.metadata.get("funnel_stats")
    if isinstance(funnel, dict) and funnel.get("total_llm_grader_results"):
        total_llm = funnel["total_llm_grader_results"]
        skipped = funnel.get("funnel_skipped", 0)
        reviewed = funnel.get("opus_reviewed", 0)
        skip_pct = (skipped / total_llm * 100) if total_llm else 0
        lines.append("  ── Funnel Stats ──")
        lines.append(f"  LLM grader evals: {total_llm}  |  Skipped: {skipped}  |  Opus reviewed: {reviewed}")
        lines.append(f"  Skip rate: {skip_pct:.0f}%")
        lines.append("")

    # Cache stats — only shown when cache metadata present
    cache_stats = run.metadata.get("cache_stats")
    if isinstance(cache_stats, dict) and cache_stats.get("total", 0) > 0:
        lines.append("  ── Cache Stats ──")
        lines.append(
            f"  Hits: {cache_stats.get('hits', 0)}  |  Misses: {cache_stats.get('misses', 0)}  "
            f"|  Hit rate: {cache_stats.get('hit_rate', 0):.0%}"
        )
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
        output_path.write_text(report, encoding="utf-8")

    return report


def junit_xml_report(run: EvalRun, output_path: Path | None = None) -> str:
    """Generate JUnit XML report for CI integration (GitHub Actions, Jenkins, etc)."""
    testsuites = Element("testsuites")
    testsuite = SubElement(
        testsuites,
        "testsuite",
        name=f"gbr-eval-{run.layer.value}",
        tests=str(run.tasks_total),
        failures=str(run.tasks_failed),
        time=str(sum(r.duration_ms for r in run.task_results) / 1000),
    )

    for result in run.task_results:
        testcase = SubElement(
            testsuite,
            "testcase",
            name=result.task_id,
            classname=f"gbr_eval.{run.layer.value}",
            time=str(result.duration_ms / 1000),
        )

        if not result.passed:
            failed_graders = [g for g in result.grader_results if not g.passed]
            messages = []
            for g in failed_graders:
                msg = f"{g.grader_type}"
                if g.field:
                    msg += f"[{g.field}]"
                msg += f": {g.details or g.error or 'failed'}"
                messages.append(msg)
            failure = SubElement(
                testcase,
                "failure",
                message=f"score={result.score:.3f}",
                type="EvalFailure",
            )
            failure.text = "\n".join(messages)

    xml_bytes = tostring(testsuites, encoding="unicode", xml_declaration=True)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(xml_bytes, encoding="utf-8")

    return xml_bytes


def ci_summary(run: EvalRun) -> str:
    """One-line summary for CI output."""
    failed_tasks = [r.task_id for r in run.task_results if not r.passed]
    prefix = f"gbr-eval[{run.project}]" if run.project != "default" else "gbr-eval"

    if run.gate_result is not None:
        gate_label = run.gate_result.value.upper().replace("_", " ")
        tier_label = run.tier.value if run.tier else "all"
        summary = (
            f"{prefix} | {run.layer.value} {tier_label} | {gate_label} | "
            f"{run.tasks_passed}/{run.tasks_total} passed | {run.overall_score:.1%}"
        )
    else:
        status = "PASSED" if run.tasks_failed == 0 else "FAILED"
        summary = f"{prefix} {status}: {run.tasks_passed}/{run.tasks_total} tasks passed ({run.overall_score:.1%})"

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
