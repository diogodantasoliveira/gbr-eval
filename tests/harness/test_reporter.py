"""Tests for report generation functions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.harness.models import EvalRun, GateResult, GraderResult, Layer, Severity, TaskResult, Tier
from gbr_eval.harness.reporter import (
    ci_summary,
    console_report,
    failed_details,
    json_report,
    junit_xml_report,
)


def _make_grader_result(
    grader_type: str = "exact_match",
    field: str | None = "cpf",
    passed: bool = True,
    score: float = 1.0,
    details: str = "ok",
    error: str | None = None,
    severity: Severity | None = None,
) -> GraderResult:
    return GraderResult(
        grader_type=grader_type,
        field=field,
        passed=passed,
        score=score,
        details=details,
        error=error,
        severity=severity,
    )


def _make_task_result(
    task_id: str = "test.task",
    passed: bool = True,
    score: float = 1.0,
    grader_results: list[GraderResult] | None = None,
    duration_ms: float = 42.0,
) -> TaskResult:
    return TaskResult(
        task_id=task_id,
        passed=passed,
        score=score,
        grader_results=grader_results or [_make_grader_result()],
        duration_ms=duration_ms,
    )


def _make_eval_run(
    layer: Layer = Layer.PRODUCT,
    tier: Tier | None = Tier.GATE,
    task_results: list[TaskResult] | None = None,
    tasks_total: int = 1,
    tasks_passed: int = 1,
    tasks_failed: int = 0,
    overall_score: float = 1.0,
    gate_result: GateResult | None = None,
    baseline_run_id: str | None = None,
) -> EvalRun:
    results = task_results if task_results is not None else [_make_task_result()]
    return EvalRun(
        run_id="abcdef12-1234-1234-1234-1234567890ab",
        layer=layer,
        tier=tier,
        tasks_total=tasks_total,
        tasks_passed=tasks_passed,
        tasks_failed=tasks_failed,
        task_results=results,
        overall_score=overall_score,
        finished_at=datetime.now(UTC),
        gate_result=gate_result,
        baseline_run_id=baseline_run_id,
    )


class TestConsoleReport:
    def test_contains_run_id_prefix(self):
        run = _make_eval_run()
        report = console_report(run)
        assert "abcdef12" in report

    def test_contains_layer(self):
        run = _make_eval_run(layer=Layer.PRODUCT)
        report = console_report(run)
        assert "product" in report

    def test_contains_tier(self):
        run = _make_eval_run(tier=Tier.GATE)
        report = console_report(run)
        assert "gate" in report

    def test_tier_none_shows_all(self):
        run = _make_eval_run(tier=None)
        report = console_report(run)
        assert "all" in report

    def test_pass_task_shown(self):
        task_result = _make_task_result(task_id="extract.cpf", passed=True, score=1.0)
        run = _make_eval_run(task_results=[task_result])
        report = console_report(run)
        assert "PASS" in report
        assert "extract.cpf" in report

    def test_fail_task_shown(self):
        grader = _make_grader_result(passed=False, score=0.0, details="mismatch")
        task_result = _make_task_result(task_id="extract.nome", passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        report = console_report(run)
        assert "FAIL" in report
        assert "extract.nome" in report

    def test_error_shown_when_present(self):
        grader = _make_grader_result(passed=False, score=0.0, error="Something broke")
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        report = console_report(run)
        assert "Something broke" in report

    def test_totals_shown(self):
        run = _make_eval_run(tasks_total=5, tasks_passed=4, tasks_failed=1, overall_score=0.8)
        report = console_report(run)
        assert "Total: 5" in report
        assert "Pass: 4" in report
        assert "Fail: 1" in report

    def test_overall_score_shown_as_percent(self):
        run = _make_eval_run(overall_score=0.8)
        report = console_report(run)
        assert "80.0%" in report

    def test_grader_field_shown_in_brackets(self):
        grader = _make_grader_result(grader_type="exact_match", field="matricula", passed=True)
        task_result = _make_task_result(grader_results=[grader])
        run = _make_eval_run(task_results=[task_result])
        report = console_report(run)
        assert "[matricula]" in report

    def test_grader_no_field_omits_brackets(self):
        grader = _make_grader_result(grader_type="field_f1", field=None, passed=True)
        task_result = _make_task_result(grader_results=[grader])
        run = _make_eval_run(task_results=[task_result])
        report = console_report(run)
        # No bracket for field-less grader
        assert "field_f1:" in report

    def test_returns_string(self):
        run = _make_eval_run()
        assert isinstance(console_report(run), str)


class TestJsonReport:
    def test_returns_valid_json(self):
        run = _make_eval_run()
        report = json_report(run)
        data = json.loads(report)
        assert isinstance(data, dict)

    def test_contains_run_id(self):
        run = _make_eval_run()
        report = json_report(run)
        data = json.loads(report)
        assert data["run_id"] == "abcdef12-1234-1234-1234-1234567890ab"

    def test_contains_task_results(self):
        run = _make_eval_run()
        report = json_report(run)
        data = json.loads(report)
        assert "task_results" in data
        assert len(data["task_results"]) == 1

    def test_writes_to_file_when_path_given(self, tmp_path: Path):
        run = _make_eval_run()
        output_path = tmp_path / "report.json"
        json_report(run, output_path=output_path)
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "run_id" in data

    def test_creates_parent_dirs(self, tmp_path: Path):
        run = _make_eval_run()
        output_path = tmp_path / "nested" / "dir" / "report.json"
        json_report(run, output_path=output_path)
        assert output_path.exists()

    def test_no_file_written_without_path(self, tmp_path: Path):
        run = _make_eval_run()
        json_report(run, output_path=None)
        # No side-effects — directory should be empty
        assert list(tmp_path.iterdir()) == []


class TestJunitXmlReport:
    def test_returns_xml_string(self):
        run = _make_eval_run()
        xml = junit_xml_report(run)
        assert xml.startswith("<?xml")
        assert "<testsuites" in xml

    def test_contains_testsuite_name(self):
        run = _make_eval_run(layer=Layer.PRODUCT)
        xml = junit_xml_report(run)
        assert "gbr-eval-product" in xml

    def test_passed_task_has_no_failure_element(self):
        task_result = _make_task_result(passed=True)
        run = _make_eval_run(task_results=[task_result])
        xml = junit_xml_report(run)
        assert "<failure" not in xml

    def test_failed_task_has_failure_element(self):
        grader = _make_grader_result(passed=False, score=0.0, details="wrong value")
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        xml = junit_xml_report(run)
        assert "<failure" in xml

    def test_failure_message_includes_grader_details(self):
        grader = _make_grader_result(passed=False, score=0.0, details="cpf mismatch")
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        xml = junit_xml_report(run)
        assert "cpf mismatch" in xml

    def test_failure_message_includes_error_when_no_details(self):
        grader = _make_grader_result(passed=False, score=0.0, details="", error="API timeout")
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        xml = junit_xml_report(run)
        assert "API timeout" in xml

    def test_writes_to_file_when_path_given(self, tmp_path: Path):
        run = _make_eval_run()
        output_path = tmp_path / "results.xml"
        junit_xml_report(run, output_path=output_path)
        assert output_path.exists()
        assert "<?xml" in output_path.read_text()

    def test_task_count_in_testsuite(self):
        results = [_make_task_result(task_id=f"task.{i}") for i in range(3)]
        run = _make_eval_run(task_results=results, tasks_total=3, tasks_passed=3)
        xml = junit_xml_report(run)
        assert 'tests="3"' in xml


class TestCiSummary:
    def test_passed_when_no_failures(self):
        run = _make_eval_run(tasks_total=3, tasks_passed=3, tasks_failed=0, overall_score=1.0)
        summary = ci_summary(run)
        assert "PASSED" in summary

    def test_failed_when_any_failure(self):
        grader = _make_grader_result(passed=False, score=0.0)
        task_result = _make_task_result(task_id="fail.task", passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(
            task_results=[task_result], tasks_total=1, tasks_passed=0, tasks_failed=1, overall_score=0.0,
        )
        summary = ci_summary(run)
        assert "FAILED" in summary

    def test_shows_pass_count(self):
        run = _make_eval_run(tasks_total=5, tasks_passed=4, tasks_failed=1, overall_score=0.8)
        summary = ci_summary(run)
        assert "4/5" in summary

    def test_shows_overall_score_percent(self):
        run = _make_eval_run(tasks_total=2, tasks_passed=1, tasks_failed=1, overall_score=0.5)
        summary = ci_summary(run)
        assert "50.0%" in summary

    def test_failed_task_ids_listed(self):
        grader = _make_grader_result(passed=False, score=0.0)
        task_result = _make_task_result(task_id="extract.cpf", passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(
            task_results=[task_result], tasks_total=1, tasks_passed=0, tasks_failed=1, overall_score=0.0,
        )
        summary = ci_summary(run)
        assert "extract.cpf" in summary

    def test_no_failed_section_when_all_pass(self):
        run = _make_eval_run(tasks_total=1, tasks_passed=1, tasks_failed=0, overall_score=1.0)
        summary = ci_summary(run)
        assert "Failed:" not in summary


class TestFailedDetails:
    def test_empty_when_all_pass(self):
        run = _make_eval_run()
        details = failed_details(run)
        assert details == []

    def test_returns_failed_tasks(self):
        grader = _make_grader_result(passed=False, score=0.0, details="bad value")
        task_result = _make_task_result(task_id="check.cpf", passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        details = failed_details(run)
        assert len(details) == 1
        assert details[0]["task_id"] == "check.cpf"

    def test_score_included_in_detail(self):
        grader = _make_grader_result(passed=False, score=0.0)
        task_result = _make_task_result(passed=False, score=0.3, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.3)
        details = failed_details(run)
        assert details[0]["score"] == 0.3

    def test_failed_graders_nested(self):
        grader_pass = _make_grader_result(grader_type="exact_match", field="cpf", passed=True)
        grader_fail = _make_grader_result(grader_type="regex_match", field="cnpj", passed=False, score=0.0)
        task_result = _make_task_result(passed=False, score=0.5, grader_results=[grader_pass, grader_fail])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.5)
        details = failed_details(run)
        failed_graders = details[0]["failed_graders"]
        assert isinstance(failed_graders, list)
        assert len(failed_graders) == 1
        assert failed_graders[0]["type"] == "regex_match"

    def test_skips_passed_tasks(self):
        pass_result = _make_task_result(task_id="ok.task", passed=True)
        fail_grader = _make_grader_result(passed=False, score=0.0)
        fail_result = _make_task_result(task_id="fail.task", passed=False, score=0.0, grader_results=[fail_grader])
        run = _make_eval_run(
            task_results=[pass_result, fail_result],
            tasks_total=2,
            tasks_passed=1,
            tasks_failed=1,
            overall_score=0.5,
        )
        details = failed_details(run)
        assert len(details) == 1
        assert details[0]["task_id"] == "fail.task"


class TestConsoleReportGateResult:
    def test_gate_result_shown_in_header(self):
        run = _make_eval_run(gate_result=GateResult.GO)
        report = console_report(run)
        assert "Gate: GO" in report

    def test_conditional_go_shown(self):
        run = _make_eval_run(gate_result=GateResult.CONDITIONAL_GO)
        report = console_report(run)
        assert "CONDITIONAL GO" in report

    def test_no_gate_result_omits_gate_line(self):
        run = _make_eval_run(gate_result=None)
        report = console_report(run)
        assert "Gate:" not in report


class TestConsoleReportSeverity:
    def test_severity_grouping_shown_when_failures_have_severity(self):
        grader = _make_grader_result(passed=False, score=0.0, details="mismatch", severity=Severity.CRITICAL)
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        report = console_report(run)
        assert "CRITICAL (1):" in report

    def test_severity_not_shown_when_no_severity_set(self):
        grader = _make_grader_result(passed=False, score=0.0, details="mismatch")
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        report = console_report(run)
        assert "Failures by Severity" not in report

    def test_multiple_severities_in_order(self):
        g_crit = _make_grader_result(field="cpf", passed=False, score=0.0, details="wrong", severity=Severity.CRITICAL)
        g_high = _make_grader_result(field="area", passed=False, score=0.0, details="wrong", severity=Severity.HIGH)
        task_result = _make_task_result(passed=False, score=0.0, grader_results=[g_crit, g_high])
        run = _make_eval_run(task_results=[task_result], tasks_passed=0, tasks_failed=1, overall_score=0.0)
        report = console_report(run)
        crit_pos = report.index("CRITICAL")
        high_pos = report.index("HIGH")
        assert crit_pos < high_pos


class TestConsoleReportRegressionDelta:
    def test_regression_delta_shown_when_present(self):
        from gbr_eval.harness.regression import RegressionDelta
        run = _make_eval_run(baseline_run_id="xyz789")
        delta = RegressionDelta(
            baseline_run_id="xyz789", current_run_id="abc123",
            newly_passing=["task.a"], score_deltas={"task.a": 0.4},
        )
        report = console_report(run, delta=delta)
        assert "Regression Delta" in report
        assert "No regressions detected" in report

    def test_regression_detected_shown(self):
        from gbr_eval.harness.regression import RegressionDelta
        run = _make_eval_run(baseline_run_id="xyz789")
        delta = RegressionDelta(
            baseline_run_id="xyz789", current_run_id="abc123",
            newly_failing=["task.b"], score_deltas={"task.b": -0.3},
            has_regressions=True,
        )
        report = console_report(run, delta=delta)
        assert "REGRESSIONS DETECTED" in report
        assert "task.b" in report

    def test_no_delta_no_section(self):
        run = _make_eval_run()
        report = console_report(run)
        assert "Regression Delta" not in report


class TestCiSummaryGateResult:
    def test_gate_result_in_ci_summary(self):
        run = _make_eval_run(gate_result=GateResult.CONDITIONAL_GO, layer=Layer.PRODUCT, tier=Tier.GATE)
        summary = ci_summary(run)
        assert "CONDITIONAL GO" in summary
        assert "product" in summary

    def test_no_gate_result_uses_old_format(self):
        run = _make_eval_run(gate_result=None)
        summary = ci_summary(run)
        assert "PASSED" in summary

    def test_failed_tasks_appended_with_gate(self):
        grader = _make_grader_result(passed=False, score=0.0)
        task_result = _make_task_result(task_id="fail.task", passed=False, score=0.0, grader_results=[grader])
        run = _make_eval_run(
            task_results=[task_result], tasks_total=1, tasks_passed=0, tasks_failed=1,
            overall_score=0.0, gate_result=GateResult.NO_GO,
        )
        summary = ci_summary(run)
        assert "fail.task" in summary


class TestSeverityInJsonReport:
    def test_severity_included_when_set(self):
        import json as json_mod
        grader = _make_grader_result(severity=Severity.HIGH)
        task_result = _make_task_result(grader_results=[grader])
        run = _make_eval_run(task_results=[task_result])
        data = json_mod.loads(json_report(run))
        assert data["task_results"][0]["grader_results"][0]["severity"] == "high"

    def test_severity_null_when_not_set(self):
        import json as json_mod
        grader = _make_grader_result()
        task_result = _make_task_result(grader_results=[grader])
        run = _make_eval_run(task_results=[task_result])
        data = json_mod.loads(json_report(run))
        assert data["task_results"][0]["grader_results"][0]["severity"] is None

    def test_gate_result_in_json(self):
        import json as json_mod
        run = _make_eval_run(gate_result=GateResult.GO)
        data = json_mod.loads(json_report(run))
        assert data["gate_result"] == "go"
