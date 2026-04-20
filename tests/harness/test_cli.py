"""Tests for the Click CLI entry point (runner.py)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from click.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.harness.models import EvalRun, GraderResult, Layer, TaskResult
from gbr_eval.harness.runner import cli


def _make_eval_run(
    task_id: str = "test.task",
    score: float = 1.0,
    passed: bool = True,
    started_at: datetime | None = None,
) -> EvalRun:
    """Build a minimal EvalRun with a single TaskResult for fixture use."""
    grader_result = GraderResult(
        grader_type="exact_match",
        field="cpf",
        passed=passed,
        score=score,
        weight=1.0,
    )
    task_result = TaskResult(
        task_id=task_id,
        passed=passed,
        score=score,
        grader_results=[grader_result],
        duration_ms=10.0,
        pass_threshold=0.95,
    )
    return EvalRun(
        run_id=str(uuid.uuid4()),
        layer=Layer.PRODUCT,
        tasks_total=1,
        tasks_passed=1 if passed else 0,
        tasks_failed=0 if passed else 1,
        task_results=[task_result],
        overall_score=score,
        started_at=started_at or datetime.now(UTC),
        finished_at=datetime.now(UTC),
    )


def _write_run_json(runs_dir: Path, eval_run: EvalRun) -> None:
    """Serialize an EvalRun to a JSON file in runs_dir."""
    file_path = runs_dir / f"run_{eval_run.run_id}.json"
    file_path.write_text(eval_run.model_dump_json())


def _write_task_yaml(path: Path, task_id: str = "test.cli", layer: str = "product") -> Path:
    yaml_content = f"""
task_id: {task_id}
category: extraction
component: ai-engine
layer: {layer}
tier: gate

input:
  endpoint: /api/v1/extract

expected:
  cpf: "123.456.789-09"

graders:
  - type: exact_match
    field: cpf
    weight: 1.0
    required: false

scoring_mode: weighted
pass_threshold: 0.50
"""
    task_file = path / f"{task_id}.yaml"
    task_file.write_text(yaml_content)
    return task_file


class TestCliVersion:
    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_prog_name_in_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert "gbr-eval" in result.output


class TestCliHelp:
    def test_help_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "gbr-eval" in result.output

    def test_run_subcommand_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "--suite" in result.output
        assert "--task" in result.output


class TestCliRunNoArgs:
    def test_no_suite_or_task_raises_usage_error(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run"])
        assert result.exit_code != 0
        assert "Provide --suite or --task" in result.output


class TestCliRunSingleTask:
    def test_run_task_console_output(self, tmp_path: Path):
        task_file = _write_task_yaml(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--task", str(task_file)])
        assert result.exit_code == 0
        # console_report header
        assert "Eval Run" in result.output

    def test_run_task_json_output(self, tmp_path: Path):
        task_file = _write_task_yaml(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--task", str(task_file), "--output-format", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert "run_id" in data
        assert "task_results" in data

    def test_run_task_json_to_file(self, tmp_path: Path):
        task_file = _write_task_yaml(tmp_path)
        output_file = tmp_path / "out.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["run", "--task", str(task_file), "--output-format", "json", "--output-file", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        import json
        data = json.loads(output_file.read_text())
        assert "run_id" in data

    def test_run_task_ci_summary_in_console(self, tmp_path: Path):
        task_file = _write_task_yaml(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--task", str(task_file)])
        assert result.exit_code == 0
        # ci_summary line is always echoed in console mode
        assert "gbr-eval" in result.output


class TestCliRunSuite:
    def test_run_suite_console_output(self, tmp_path: Path):
        suite_dir = tmp_path / "suite"
        suite_dir.mkdir()
        _write_task_yaml(suite_dir, task_id="suite.task1")
        _write_task_yaml(suite_dir, task_id="suite.task2")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--suite", str(suite_dir)])
        assert result.exit_code == 0
        assert "Total: 2" in result.output

    def test_run_suite_with_layer_filter(self, tmp_path: Path):
        suite_dir = tmp_path / "suite"
        suite_dir.mkdir()
        _write_task_yaml(suite_dir, task_id="product.task", layer="product")
        _write_task_yaml(suite_dir, task_id="engineering.task", layer="engineering")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--suite", str(suite_dir), "--layer", "product"])
        assert result.exit_code == 0
        assert "product.task" in result.output
        assert "engineering.task" not in result.output

    def test_run_suite_with_tier_filter(self, tmp_path: Path):
        suite_dir = tmp_path / "suite"
        suite_dir.mkdir()
        # Both tasks are tier=gate by default in the helper
        _write_task_yaml(suite_dir, task_id="gate.task")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--suite", str(suite_dir), "--tier", "gate"])
        assert result.exit_code == 0
        assert "gate.task" in result.output

    def test_run_suite_json_output(self, tmp_path: Path):
        suite_dir = tmp_path / "suite"
        suite_dir.mkdir()
        _write_task_yaml(suite_dir, task_id="json.task")
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--suite", str(suite_dir), "--output-format", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert "task_results" in data

    def test_run_empty_suite_returns_zero_tasks(self, tmp_path: Path):
        suite_dir = tmp_path / "empty_suite"
        suite_dir.mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--suite", str(suite_dir)])
        assert result.exit_code == 0
        assert "Total: 0" in result.output

    def test_run_suite_nonexistent_path_fails(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--suite", str(tmp_path / "does_not_exist")])
        assert result.exit_code != 0


class TestCliSelfEval:
    def test_cli_self_eval_with_golden_dir(self, tmp_path: Path):
        import json

        # Task suite directory
        suite_dir = tmp_path / "tasks" / "product"
        suite_dir.mkdir(parents=True)

        # Write a task YAML that references document_type via payload skill
        task_yaml = """\
task_id: extraction.matricula.cpf
category: extraction
component: ai-engine
layer: product
tier: gate

input:
  endpoint: /api/v1/extract
  payload:
    skill: matricula_v1

expected:
  cpf: "123.456.789-09"

graders:
  - type: exact_match
    field: cpf
    weight: 1.0
    required: false

scoring_mode: weighted
pass_threshold: 0.50
"""
        (suite_dir / "matricula_cpf.yaml").write_text(task_yaml)

        # Golden dir with one case for the matricula document type
        golden_dir = tmp_path / "golden"
        matricula_dir = golden_dir / "matricula"
        matricula_dir.mkdir(parents=True)
        case = {
            "case_number": 1,
            "tags": ["seed"],
            "expected_output": {"cpf": "123.456.789-09"},
        }
        (matricula_dir / "case_001.json").write_text(json.dumps(case))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "run",
                "--suite", str(suite_dir),
                "--golden-dir", str(golden_dir),
                "--self-eval",
                "--tier", "gate",
                "--output-format", "json",
            ],
        )

        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "gate_result" in data


class TestCliMutualExclusion:
    def test_cli_self_eval_and_endpoint_mutually_exclusive(self, tmp_path: Path):
        """--self-eval and --endpoint cannot be used together."""
        suite_dir = tmp_path / "tasks" / "product"
        suite_dir.mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, [
            "run",
            "--suite", str(suite_dir),
            "--golden-dir", str(tmp_path),
            "--self-eval",
            "--endpoint", "http://localhost:8000",
            "--output-format", "json",
        ])
        assert result.exit_code != 0
        combined = (result.output or "") + str(result.exception or "")
        assert "mutually exclusive" in combined.lower()


class TestCliTrends:
    def test_trends_no_runs(self, tmp_path: Path):
        """Empty runs dir exits cleanly and reports no alerts."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["trends", "--runs-dir", str(runs_dir)])
        assert result.exit_code == 0
        assert "No trend alerts" in result.output

    def test_trends_with_stable_scores(self, tmp_path: Path):
        """Three runs with identical scores should produce no trend alerts."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        base_time = datetime.now(UTC)
        for i in range(3):
            run = _make_eval_run(
                task_id="extraction.cpf",
                score=1.0,
                passed=True,
                started_at=base_time + timedelta(hours=i),
            )
            _write_run_json(runs_dir, run)

        runner = CliRunner()
        result = runner.invoke(cli, ["trends", "--runs-dir", str(runs_dir)])
        assert result.exit_code == 0
        assert "No trend alerts" in result.output

    def test_trends_json_output(self, tmp_path: Path):
        """--output-format json produces valid JSON with expected keys."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        base_time = datetime.now(UTC)
        for i in range(3):
            run = _make_eval_run(
                task_id="extraction.cpf",
                score=1.0,
                started_at=base_time + timedelta(hours=i),
            )
            _write_run_json(runs_dir, run)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["trends", "--runs-dir", str(runs_dir), "--output-format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "analyzed_runs" in data
        assert "trend_alerts" in data
        assert data["analyzed_runs"] == 3

    def test_trends_detects_decline(self, tmp_path: Path):
        """Three runs with strictly declining scores should produce a declining alert."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        base_time = datetime.now(UTC)
        scores = [0.90, 0.80, 0.70]
        for i, score in enumerate(scores):
            run = _make_eval_run(
                task_id="extraction.cpf",
                score=score,
                passed=score >= 0.95,
                started_at=base_time + timedelta(hours=i),
            )
            _write_run_json(runs_dir, run)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["trends", "--runs-dir", str(runs_dir), "--output-format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        alerts = data["trend_alerts"]
        assert len(alerts) >= 1
        directions = [a["direction"] for a in alerts]
        assert "declining" in directions


class TestCliAnalyze:
    def test_analyze_no_runs(self, tmp_path: Path):
        """Empty runs dir exits cleanly with a 'No runs found' message."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--runs-dir", str(runs_dir)])
        assert result.exit_code == 0
        assert "No runs found" in result.output

    def test_analyze_console_output(self, tmp_path: Path):
        """Runs with results produce analysis output containing key sections."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        base_time = datetime.now(UTC)
        for i in range(2):
            run = _make_eval_run(
                task_id="extraction.cpf",
                score=0.80,
                passed=False,
                started_at=base_time + timedelta(hours=i),
            )
            _write_run_json(runs_dir, run)

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--runs-dir", str(runs_dir)])
        assert result.exit_code == 0
        # format_analysis always starts with this header
        assert "Eval Analysis" in result.output
        assert "extraction.cpf" in result.output

    def test_analyze_json_output(self, tmp_path: Path):
        """--output-format json produces valid JSON with expected top-level keys."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run = _make_eval_run(task_id="extraction.cpf", score=1.0, passed=True)
        _write_run_json(runs_dir, run)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["analyze", "--runs-dir", str(runs_dir), "--output-format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "runs_analyzed" in data
        assert "task_stats" in data
        assert "weakest_tasks" in data
        assert "most_failing_fields" in data
        assert data["runs_analyzed"] == 1

    def test_analyze_top_option(self, tmp_path: Path):
        """--top N limits the number of results in JSON output."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        base_time = datetime.now(UTC)
        # Create runs with 5 distinct tasks that fail
        for i in range(5):
            run = _make_eval_run(
                task_id=f"task.failing.{i}",
                score=0.50,
                passed=False,
                started_at=base_time + timedelta(hours=i),
            )
            _write_run_json(runs_dir, run)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["analyze", "--runs-dir", str(runs_dir), "--top", "2", "--output-format", "json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        # weakest_tasks is limited to --top N
        assert len(data["weakest_tasks"]) <= 2
