"""Tests for analyze_runs, format_analysis, and analysis_to_dict."""

from __future__ import annotations

from gbr_eval.harness.analyzer import analysis_to_dict, analyze_runs, format_analysis
from gbr_eval.harness.models import EvalRun, GraderResult, Layer, TaskResult


def _make_grader_result(
    grader_type: str = "exact_match",
    field: str | None = "cpf",
    passed: bool = True,
    score: float = 1.0,
) -> GraderResult:
    return GraderResult(
        grader_type=grader_type,
        field=field,
        passed=passed,
        score=score,
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
        task_results=task_results,
        overall_score=overall_score,
    )


class TestAnalyzeRuns:
    def test_analyze_single_run(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])

        report = analyze_runs([run])

        assert report.runs_analyzed == 1
        assert len(report.task_stats) == 1
        task_stat = report.task_stats[0]
        assert task_stat.task_id == "task.A"
        assert task_stat.run_count == 1
        assert task_stat.pass_count == 1
        assert task_stat.pass_rate == 1.0
        assert task_stat.avg_score == 1.0

    def test_analyze_identifies_weakest_tasks(self) -> None:
        tr_pass = _make_task_result("task.pass", passed=True, score=1.0)
        tr_fail = _make_task_result("task.fail", passed=False, score=0.5)
        run = _make_eval_run("run-1", [tr_pass, tr_fail])

        report = analyze_runs([run])

        weakest_ids = [t.task_id for t in report.weakest_tasks]
        assert "task.fail" in weakest_ids
        assert "task.pass" not in weakest_ids

    def test_analyze_empty_runs(self) -> None:
        report = analyze_runs([])

        assert report.runs_analyzed == 0
        assert report.task_stats == []
        assert report.weakest_tasks == []
        assert report.most_failing_fields == []

    def test_analyze_aggregates_multiple_runs_for_same_task(self) -> None:
        tr1 = _make_task_result("task.A", passed=True, score=1.0)
        tr2 = _make_task_result("task.A", passed=False, score=0.5)
        run1 = _make_eval_run("run-1", [tr1])
        run2 = _make_eval_run("run-2", [tr2])

        report = analyze_runs([run1, run2])

        assert len(report.task_stats) == 1
        ts = report.task_stats[0]
        assert ts.run_count == 2
        assert ts.pass_count == 1
        assert ts.pass_rate == 0.5
        assert ts.avg_score == 0.75

    def test_analyze_tracks_failing_fields(self) -> None:
        failing_grader = _make_grader_result(field="nome", passed=False, score=0.0)
        tr = _make_task_result(
            "task.A", passed=False, score=0.0, grader_results=[failing_grader]
        )
        run = _make_eval_run("run-1", [tr])

        report = analyze_runs([run])

        failing_fields = [f.field_name for f in report.most_failing_fields]
        assert "nome" in failing_fields

    def test_analyze_all_pass_no_weakest(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])

        report = analyze_runs([run])

        assert report.weakest_tasks == []


class TestFormatAnalysis:
    def test_format_analysis_produces_output(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])
        report = analyze_runs([run])

        formatted = format_analysis(report)

        assert len(formatted) > 0

    def test_format_analysis_includes_task_ids(self) -> None:
        tr = _make_task_result("task.unique_id", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])
        report = analyze_runs([run])

        formatted = format_analysis(report)

        assert "task.unique_id" in formatted

    def test_format_analysis_mentions_runs_analyzed(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])
        report = analyze_runs([run])

        formatted = format_analysis(report)

        assert "1 runs analyzed" in formatted

    def test_format_analysis_empty_runs(self) -> None:
        report = analyze_runs([])

        formatted = format_analysis(report)

        assert len(formatted) > 0


class TestAnalysisToDict:
    def test_analysis_to_dict_has_required_keys(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])
        report = analyze_runs([run])

        result = analysis_to_dict(report)

        assert "runs_analyzed" in result
        assert "task_stats" in result
        assert "weakest_tasks" in result
        assert "most_failing_fields" in result

    def test_analysis_to_dict_task_stats_structure(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run = _make_eval_run("run-1", [tr])
        report = analyze_runs([run])

        result = analysis_to_dict(report)

        assert len(result["task_stats"]) == 1
        ts = result["task_stats"][0]
        assert "task_id" in ts
        assert "run_count" in ts
        assert "pass_rate" in ts
        assert "avg_score" in ts
        assert "min_score" in ts
        assert "p5_score" in ts

    def test_analysis_to_dict_runs_analyzed_count(self) -> None:
        tr = _make_task_result("task.A", passed=True, score=1.0)
        run1 = _make_eval_run("run-1", [tr])
        run2 = _make_eval_run("run-2", [tr])
        report = analyze_runs([run1, run2])

        result = analysis_to_dict(report)

        assert result["runs_analyzed"] == 2

    def test_analysis_to_dict_weakest_tasks_structure(self) -> None:
        tr = _make_task_result("task.weak", passed=False, score=0.4)
        run = _make_eval_run("run-1", [tr])
        report = analyze_runs([run])

        result = analysis_to_dict(report)

        assert len(result["weakest_tasks"]) == 1
        wt = result["weakest_tasks"][0]
        assert "task_id" in wt
        assert "pass_rate" in wt
        assert "avg_score" in wt
