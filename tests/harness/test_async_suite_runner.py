"""Tests for async suite runner (parallel task execution)."""

from __future__ import annotations

import asyncio

import gbr_eval.graders  # noqa: F401 — trigger auto-registration
from gbr_eval.harness.async_suite_runner import run_eval_run_async, run_suite_async
from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.runner import run_task


def _make_task(task_id: str, expected: dict[str, object], **kwargs: object) -> Task:
    defaults: dict[str, object] = {
        "task_id": task_id,
        "category": Category.EXTRACTION,
        "component": "test",
        "layer": Layer.PRODUCT,
        "tier": Tier.GATE,
        "input": TaskInput(),
        "expected": expected,
        "graders": [
            GraderSpec(type="exact_match", field=list(expected.keys())[0], weight=1.0),
        ],
        "scoring_mode": ScoringMode.WEIGHTED,
        "pass_threshold": 0.95,
    }
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


def test_async_suite_runner_produces_same_results() -> None:
    """Async and sync runners must produce identical results for deterministic tasks."""
    tasks = [
        _make_task("task.a", {"cpf": "123.456.789-09"}),
        _make_task("task.b", {"nome": "Joao Silva"}),
        _make_task("task.c", {"status": "aprovado"}),
    ]
    outputs = {
        "task.a": {"cpf": "123.456.789-09"},   # passes
        "task.b": {"nome": "wrong"},            # fails
        "task.c": {"status": "aprovado"},       # passes
    }

    # Sync baseline
    sync_results = [run_task(task, outputs.get(task.task_id, {})) for task in tasks]

    # Async parallel
    async_results = asyncio.run(run_suite_async(tasks, outputs))

    assert len(async_results) == len(sync_results)
    for sync_r, async_r in zip(sync_results, async_results, strict=True):
        assert async_r.task_id == sync_r.task_id
        assert async_r.passed == sync_r.passed
        assert async_r.score == sync_r.score
        assert len(async_r.grader_results) == len(sync_r.grader_results)


def test_async_suite_runner_empty_tasks() -> None:
    """Empty task list returns an empty result list."""
    results = asyncio.run(run_suite_async([], {}))
    assert results == []


def test_async_suite_runner_missing_output_defaults_to_empty() -> None:
    """Tasks with no entry in outputs dict are evaluated against empty output."""
    task = _make_task("task.missing", {"cpf": "123.456.789-09"})
    results = asyncio.run(run_suite_async([task], {}))
    assert len(results) == 1
    # exact_match against empty output → fail
    assert not results[0].passed
    assert results[0].score == 0.0


def test_async_suite_runner_respects_concurrency_limit() -> None:
    """max_concurrency=1 must still complete all tasks correctly."""
    tasks = [
        _make_task("task.seq.a", {"x": "1"}),
        _make_task("task.seq.b", {"x": "2"}),
        _make_task("task.seq.c", {"x": "3"}),
    ]
    outputs = {
        "task.seq.a": {"x": "1"},
        "task.seq.b": {"x": "2"},
        "task.seq.c": {"x": "3"},
    }
    results = asyncio.run(run_suite_async(tasks, outputs, max_concurrency=1))
    assert len(results) == 3
    assert all(r.passed for r in results)


def test_run_eval_run_async_gate_classification() -> None:
    """run_eval_run_async returns a fully classified EvalRun."""
    tasks = [
        _make_task("task.eval.a", {"val": "ok"}),
        _make_task("task.eval.b", {"val": "ok"}),
    ]
    outputs = {
        "task.eval.a": {"val": "ok"},
        "task.eval.b": {"val": "ok"},
    }
    eval_run = asyncio.run(run_eval_run_async(tasks, outputs, layer=Layer.PRODUCT))

    assert eval_run.tasks_total == 2
    assert eval_run.tasks_passed == 2
    assert eval_run.tasks_failed == 0
    assert eval_run.overall_score == 1.0
    assert eval_run.gate_result is not None
    assert eval_run.finished_at is not None
