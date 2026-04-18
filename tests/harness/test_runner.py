"""Tests for the eval harness runner."""

from pathlib import Path

import pytest

from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.runner import load_task, run_task

import gbr_eval.graders.deterministic  # noqa: F401


FIXTURES = Path(__file__).parent / "fixtures"


class TestRunTask:
    def _make_task(self, graders: list[GraderSpec], scoring_mode: ScoringMode = ScoringMode.WEIGHTED) -> Task:
        return Task(
            task_id="test.task",
            category=Category.EXTRACTION,
            component="test",
            layer=Layer.L1,
            tier=Tier.GATE,
            input=TaskInput(),
            expected={"cpf": "123.456.789-09", "nome": "João"},
            graders=graders,
            scoring_mode=scoring_mode,
            pass_threshold=0.95,
        )

    def test_all_pass(self):
        task = self._make_task([
            GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True),
            GraderSpec(type="exact_match", field="nome", weight=2.0),
        ])
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert result.passed
        assert result.score == 1.0
        assert len(result.grader_results) == 2

    def test_required_fails(self):
        task = self._make_task([
            GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True),
            GraderSpec(type="exact_match", field="nome", weight=2.0),
        ])
        output = {"cpf": "WRONG", "nome": "João"}
        result = run_task(task, output)
        assert not result.passed

    def test_weighted_scoring(self):
        task = self._make_task([
            GraderSpec(type="exact_match", field="cpf", weight=3.0),
            GraderSpec(type="exact_match", field="nome", weight=1.0),
        ])
        output = {"cpf": "123.456.789-09", "nome": "WRONG"}
        result = run_task(task, output)
        assert result.score == pytest.approx(0.75)

    def test_binary_scoring(self):
        task = self._make_task(
            [
                GraderSpec(type="exact_match", field="cpf"),
                GraderSpec(type="exact_match", field="nome"),
            ],
            scoring_mode=ScoringMode.BINARY,
        )
        output = {"cpf": "123.456.789-09", "nome": "WRONG"}
        result = run_task(task, output)
        assert result.score == 0.0

    def test_hybrid_scoring_required_fails(self):
        task = self._make_task(
            [
                GraderSpec(type="exact_match", field="cpf", required=True),
                GraderSpec(type="exact_match", field="nome"),
            ],
            scoring_mode=ScoringMode.HYBRID,
        )
        output = {"cpf": "WRONG", "nome": "João"}
        result = run_task(task, output)
        assert result.score == 0.0

    def test_unknown_grader_returns_error(self):
        task = self._make_task([
            GraderSpec(type="nonexistent_grader", field="cpf"),
        ])
        result = run_task(task, {"cpf": "123"})
        assert not result.passed
        assert result.grader_results[0].error is not None


class TestLoadTask:
    def test_load_yaml(self, tmp_path: Path):
        yaml_content = """
task_id: test.load
category: extraction
component: ai-engine
layer: L2
tier: gate

input:
  endpoint: /api/v1/extract

expected:
  cpf: "123"

graders:
  - type: exact_match
    field: cpf
    weight: 3
    required: true

scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = tmp_path / "test.yaml"
        task_file.write_text(yaml_content)

        task = load_task(task_file)
        assert task.task_id == "test.load"
        assert task.layer == Layer.L2
        assert len(task.graders) == 1
        assert task.graders[0].required is True
