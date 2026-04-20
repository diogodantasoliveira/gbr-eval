"""Tests for epochs + score reducers (Pattern 1 from inspect_ai)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
from pydantic import ValidationError

import gbr_eval.graders  # noqa: F401
from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    ScoreReducer,
    ScoringMode,
    Task,
    TaskInput,
    TaskResult,
    Tier,
)
from gbr_eval.harness.runner import (
    _all_graders_deterministic,
    _reduce_scores,
    load_task,
    run_task,
)


def _make_task(**kwargs: object) -> Task:
    defaults: dict[str, object] = {
        "task_id": "test.epochs",
        "category": Category.EXTRACTION,
        "component": "test",
        "layer": Layer.PRODUCT,
        "tier": Tier.GATE,
        "input": TaskInput(),
        "expected": {"cpf": "123.456.789-09", "nome": "João"},
        "graders": [
            GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True),
            GraderSpec(type="exact_match", field="nome", weight=1.0),
        ],
        "scoring_mode": ScoringMode.WEIGHTED,
        "pass_threshold": 0.95,
    }
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


# --- Model validation ---


class TestTaskEpochsValidation:
    def test_default_epochs_is_one(self) -> None:
        task = _make_task()
        assert task.epochs == 1

    def test_default_reducers_is_mean(self) -> None:
        task = _make_task()
        assert task.reducers == [ScoreReducer.MEAN]
        assert task.primary_reducer == ScoreReducer.MEAN

    def test_epochs_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_task(epochs=0)

    def test_epochs_over_100_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_task(epochs=101)

    def test_primary_reducer_must_be_in_list(self) -> None:
        with pytest.raises(ValidationError, match="primary_reducer"):
            _make_task(
                reducers=[ScoreReducer.MEAN],
                primary_reducer=ScoreReducer.ALL_PASS,
            )

    def test_valid_epochs_and_reducers(self) -> None:
        task = _make_task(
            epochs=5,
            reducers=[ScoreReducer.MEAN, ScoreReducer.AT_LEAST_ONE],
            primary_reducer=ScoreReducer.MEAN,
        )
        assert task.epochs == 5
        assert len(task.reducers) == 2


# --- Reducer logic ---


class TestReduceScores:
    def test_empty_list_returns_zero(self) -> None:
        assert _reduce_scores([], ScoreReducer.MEAN, 0.95) == 0.0

    def test_single_element_mean(self) -> None:
        assert _reduce_scores([0.8], ScoreReducer.MEAN, 0.95) == 0.8

    def test_mean(self) -> None:
        assert _reduce_scores([0.8, 0.9, 1.0], ScoreReducer.MEAN, 0.95) == pytest.approx(0.9)

    def test_median_odd(self) -> None:
        assert _reduce_scores([0.8, 0.9, 1.0], ScoreReducer.MEDIAN, 0.95) == 0.9

    def test_median_even(self) -> None:
        assert _reduce_scores([0.8, 0.9, 1.0, 1.0], ScoreReducer.MEDIAN, 0.95) == pytest.approx(0.95)

    def test_at_least_one_passes(self) -> None:
        result = _reduce_scores([0.5, 0.5, 0.96], ScoreReducer.AT_LEAST_ONE, 0.95)
        assert result == 1.0

    def test_at_least_one_fails(self) -> None:
        result = _reduce_scores([0.5, 0.5, 0.5], ScoreReducer.AT_LEAST_ONE, 0.95)
        assert result == 0.5

    def test_all_pass_succeeds(self) -> None:
        result = _reduce_scores([0.96, 0.97, 0.98], ScoreReducer.ALL_PASS, 0.95)
        assert result == 1.0

    def test_all_pass_fails(self) -> None:
        result = _reduce_scores([0.96, 0.96, 0.5], ScoreReducer.ALL_PASS, 0.95)
        assert result == 0.5

    def test_majority_passes(self) -> None:
        result = _reduce_scores([0.96, 0.96, 0.5], ScoreReducer.MAJORITY, 0.95)
        assert result == 1.0

    def test_majority_fails(self) -> None:
        result = _reduce_scores([0.96, 0.5, 0.5], ScoreReducer.MAJORITY, 0.95)
        assert result == pytest.approx((0.96 + 0.5 + 0.5) / 3)


# --- Determinism detection ---


class TestDeterminismDetection:
    def test_all_deterministic(self) -> None:
        task = _make_task(graders=[
            GraderSpec(type="exact_match", field="cpf"),
            GraderSpec(type="field_f1", field="nome"),
        ])
        assert _all_graders_deterministic(task) is True

    def test_has_llm_judge(self) -> None:
        task = _make_task(graders=[
            GraderSpec(type="exact_match", field="cpf"),
            GraderSpec(type="llm_judge", config={"rubric": "test"}),
        ])
        assert _all_graders_deterministic(task) is False


# --- run_task with epochs ---


class TestRunTaskEpochs:
    def test_single_epoch_unchanged_behavior(self) -> None:
        task = _make_task(epochs=1)
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert result.passed
        assert result.score == 1.0
        assert result.epoch_scores == [1.0]
        assert result.reducer_scores == {"mean": 1.0}

    def test_deterministic_short_circuit(self) -> None:
        task = _make_task(epochs=5)
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert len(result.epoch_scores) == 1
        assert result.passed

    def test_primary_reducer_determines_pass(self) -> None:
        task = _make_task(
            epochs=1,
            graders=[GraderSpec(type="exact_match", field="cpf", weight=3.0)],
            expected={"cpf": "123"},
            reducers=[ScoreReducer.MEAN, ScoreReducer.ALL_PASS],
            primary_reducer=ScoreReducer.ALL_PASS,
            pass_threshold=0.95,
        )
        output = {"cpf": "123"}
        result = run_task(task, output)
        assert result.passed
        assert "mean" in result.reducer_scores
        assert "all_pass" in result.reducer_scores

    def test_reducer_scores_all_present(self) -> None:
        task = _make_task(
            reducers=[ScoreReducer.MEAN, ScoreReducer.MEDIAN, ScoreReducer.AT_LEAST_ONE],
            primary_reducer=ScoreReducer.MEAN,
        )
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert set(result.reducer_scores.keys()) == {"mean", "median", "at_least_one"}

    def test_epoch_scores_length_matches_effective_epochs(self) -> None:
        task = _make_task(epochs=1)
        result = run_task(task, {"cpf": "123.456.789-09", "nome": "João"})
        assert len(result.epoch_scores) == 1


# --- YAML loading ---


class TestLoadTaskEpochs:
    def test_load_without_epochs_defaults(self, tmp_path: Path) -> None:
        yaml_content = """
task_id: test.no_epochs
category: extraction
component: test
layer: product
input: {}
graders:
  - type: exact_match
    field: cpf
"""
        task_file = tmp_path / "test.yaml"
        task_file.write_text(yaml_content)
        task = load_task(task_file)
        assert task.epochs == 1
        assert task.reducers == [ScoreReducer.MEAN]
        assert task.primary_reducer == ScoreReducer.MEAN

    def test_load_with_epochs_yaml(self, tmp_path: Path) -> None:
        yaml_content = """
task_id: test.with_epochs
category: extraction
component: test
layer: product
input: {}
graders:
  - type: exact_match
    field: cpf
epochs: 3
reducers: [mean, at_least_one]
primary_reducer: mean
"""
        task_file = tmp_path / "test.yaml"
        task_file.write_text(yaml_content)
        task = load_task(task_file)
        assert task.epochs == 3
        assert task.reducers == [ScoreReducer.MEAN, ScoreReducer.AT_LEAST_ONE]


# --- Backward compat ---


class TestBackwardCompatibility:
    def test_task_result_without_reducer_fields(self) -> None:
        data = {
            "task_id": "old.task",
            "passed": True,
            "score": 1.0,
            "grader_results": [],
        }
        result = TaskResult.model_validate(data)
        assert result.reducer_scores == {}
        assert result.epoch_scores == []

    def test_reduce_scores_single_element_all_reducers(self) -> None:
        for reducer in ScoreReducer:
            score = _reduce_scores([0.9], reducer, 0.95)
            assert isinstance(score, float)
