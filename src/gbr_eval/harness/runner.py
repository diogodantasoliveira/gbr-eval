"""Eval harness runner — loads tasks, runs graders, produces results."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import yaml

from gbr_eval.graders.base import grade
from gbr_eval.harness.models import (
    Category,
    EvalRun,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    TaskResult,
    Tier,
)

if TYPE_CHECKING:
    from pathlib import Path


def load_task(path: Path) -> Task:
    with open(path) as f:
        raw = yaml.safe_load(f)

    graders = [GraderSpec(**g) for g in raw.get("graders", [])]
    task_input = TaskInput(**raw.get("input", {}))

    return Task(
        task_id=raw["task_id"],
        category=Category(raw["category"]),
        component=raw.get("component", "unknown"),
        layer=Layer(raw["layer"]),
        tier=Tier(raw.get("tier", "gate")),
        tenant_profile=raw.get("tenant_profile", "global"),
        description=raw.get("description", ""),
        input=task_input,
        expected=raw.get("expected", {}),
        graders=graders,
        scoring_mode=ScoringMode(raw.get("scoring_mode", "weighted")),
        pass_threshold=float(raw.get("pass_threshold", 0.95)),
    )


def load_tasks_from_dir(directory: Path, layer: Layer | None = None, tier: Tier | None = None) -> list[Task]:
    tasks: list[Task] = []
    for yaml_file in sorted(directory.rglob("*.yaml")):
        task = load_task(yaml_file)
        if layer and task.layer != layer:
            continue
        if tier and task.tier != tier:
            continue
        tasks.append(task)
    return tasks


def run_task(task: Task, output: dict[str, Any]) -> TaskResult:
    start = time.monotonic()
    grader_results = []

    for spec in task.graders:
        result = grade(spec.type, output, task.expected, spec)
        grader_results.append(result)

    duration_ms = (time.monotonic() - start) * 1000

    score = _compute_score(grader_results, task.scoring_mode)
    any_required_failed = any(r.required and not r.passed for r in grader_results)
    passed = score >= task.pass_threshold and not any_required_failed

    return TaskResult(
        task_id=task.task_id,
        passed=passed,
        score=score,
        grader_results=grader_results,
        duration_ms=duration_ms,
    )


def _compute_score(results: list[Any], mode: ScoringMode) -> float:
    if not results:
        return 0.0

    if mode == ScoringMode.BINARY:
        return 1.0 if all(r.passed for r in results) else 0.0

    if mode == ScoringMode.WEIGHTED:
        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            return 0.0
        return sum(r.score * r.weight for r in results) / total_weight

    # HYBRID: required graders are binary, rest are weighted
    required = [r for r in results if r.required]
    optional = [r for r in results if not r.required]

    if required and not all(r.passed for r in required):
        return 0.0

    if not optional:
        return 1.0

    total_weight = sum(r.weight for r in optional)
    if total_weight == 0:
        return 1.0
    return sum(r.score * r.weight for r in optional) / total_weight


def run_suite(
    tasks_dir: Path,
    outputs: dict[str, dict[str, Any]],
    layer: Layer | None = None,
    tier: Tier | None = None,
) -> EvalRun:
    tasks = load_tasks_from_dir(tasks_dir, layer=layer, tier=tier)
    run = EvalRun(
        run_id=str(uuid.uuid4()),
        layer=layer or Layer.L1,
        tier=tier,
        tasks_total=len(tasks),
    )

    for task in tasks:
        output = outputs.get(task.task_id, {})
        result = run_task(task, output)
        run.task_results.append(result)
        if result.passed:
            run.tasks_passed += 1
        else:
            run.tasks_failed += 1

    run.finished_at = datetime.now(UTC)
    if run.tasks_total > 0:
        run.overall_score = run.tasks_passed / run.tasks_total
    return run
