"""Tests for multi-project support."""

from __future__ import annotations

from pathlib import Path

import yaml

from gbr_eval.harness.models import EvalRun, Layer, Task, Tier
from gbr_eval.harness.reporter import ci_summary, console_report
from gbr_eval.harness.runner import load_task, load_tasks_from_dir


class TestTaskProjectField:
    def test_default_project_value(self) -> None:
        task = Task(
            task_id="t1",
            category="extraction",
            component="test",
            layer=Layer.PRODUCT,
            input={},
            graders=[{"type": "exact_match"}],
        )
        assert task.project == "default"

    def test_explicit_project_value(self) -> None:
        task = Task(
            task_id="t1",
            project="caixa",
            category="extraction",
            component="test",
            layer=Layer.PRODUCT,
            input={},
            graders=[{"type": "exact_match"}],
        )
        assert task.project == "caixa"


class TestEvalRunProjectField:
    def test_default_project_value(self) -> None:
        run = EvalRun(run_id="r1", layer=Layer.PRODUCT)
        assert run.project == "default"

    def test_explicit_project_value(self) -> None:
        run = EvalRun(run_id="r1", project="caixa", layer=Layer.PRODUCT)
        assert run.project == "caixa"

    def test_project_in_json_dump(self) -> None:
        run = EvalRun(run_id="r1", project="caixa", layer=Layer.PRODUCT)
        data = run.model_dump(mode="json")
        assert data["project"] == "caixa"


class TestLoadTaskProject:
    def test_load_task_reads_project_field(self, tmp_path: Path) -> None:
        task_yaml = tmp_path / "test_task.yaml"
        task_yaml.write_text(yaml.dump({
            "task_id": "proj-test",
            "project": "caixa",
            "category": "extraction",
            "component": "test",
            "layer": "product",
            "input": {},
            "expected": {},
            "graders": [{"type": "exact_match"}],
        }))
        task = load_task(task_yaml)
        assert task.project == "caixa"

    def test_load_task_defaults_to_default(self, tmp_path: Path) -> None:
        task_yaml = tmp_path / "test_task.yaml"
        task_yaml.write_text(yaml.dump({
            "task_id": "proj-test",
            "category": "extraction",
            "component": "test",
            "layer": "product",
            "input": {},
            "expected": {},
            "graders": [{"type": "exact_match"}],
        }))
        task = load_task(task_yaml)
        assert task.project == "default"


class TestLoadTasksFromDirProjectFilter:
    def _write_task(self, directory: Path, task_id: str, project: str) -> None:
        task_file = directory / f"{task_id}.yaml"
        task_file.write_text(yaml.dump({
            "task_id": task_id,
            "project": project,
            "category": "extraction",
            "component": "test",
            "layer": "product",
            "input": {},
            "expected": {},
            "graders": [{"type": "exact_match"}],
        }))

    def test_filter_by_project(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "t1", "caixa")
        self._write_task(tmp_path, "t2", "itau")
        self._write_task(tmp_path, "t3", "caixa")

        tasks = load_tasks_from_dir(tmp_path, project="caixa")
        assert len(tasks) == 2
        assert {t.task_id for t in tasks} == {"t1", "t3"}

    def test_no_project_filter_returns_all(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "t1", "caixa")
        self._write_task(tmp_path, "t2", "itau")

        tasks = load_tasks_from_dir(tmp_path)
        assert len(tasks) == 2

    def test_filter_with_no_matches(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "t1", "caixa")
        tasks = load_tasks_from_dir(tmp_path, project="bradesco")
        assert len(tasks) == 0


class TestReporterProjectDisplay:
    def _make_run(self, project: str = "default") -> EvalRun:
        return EvalRun(
            run_id="abcdef1234567890",
            project=project,
            layer=Layer.PRODUCT,
            tier=Tier.GATE,
            tasks_total=0,
        )

    def test_console_report_shows_project_when_not_default(self) -> None:
        run = self._make_run(project="caixa")
        report = console_report(run)
        assert "Project: caixa" in report

    def test_console_report_hides_project_when_default(self) -> None:
        run = self._make_run(project="default")
        report = console_report(run)
        assert "Project:" not in report

    def test_ci_summary_includes_project_prefix(self) -> None:
        run = self._make_run(project="caixa")
        summary = ci_summary(run)
        assert summary.startswith("gbr-eval[caixa]")

    def test_ci_summary_no_prefix_when_default(self) -> None:
        run = self._make_run(project="default")
        summary = ci_summary(run)
        assert summary.startswith("gbr-eval ")
        assert "[default]" not in summary
