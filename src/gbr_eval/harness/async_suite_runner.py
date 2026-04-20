"""Async suite runner for parallel task execution.

Uses asyncio.to_thread() to run synchronous graders in a thread pool,
enabling parallel execution of independent tasks within a suite.

Graders are synchronous CPU-bound functions. asyncio.to_thread() offloads
each task to the default ThreadPoolExecutor so the event loop remains free
to schedule other coroutines while graders are running.

The semaphore cap (max_concurrency) prevents unbounded thread creation when
suites contain many tasks. Default of 5 matches typical LLM-judge rate limits.

See also:
    gbr_eval.harness.runner._compute_task_result  — sync computation core
    gbr_eval.harness.async_runner                 — solver-based async runner
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import gbr_eval.graders  # noqa: F401 — trigger auto-registration
from gbr_eval.harness.models import EvalRun, Layer, Task, TaskResult
from gbr_eval.harness.regression import classify_gate
from gbr_eval.harness.runner import _compute_task_result


async def run_suite_async(
    tasks: list[Task],
    outputs: dict[str, dict[str, Any]],
    *,
    model_roles: dict[str, str] | None = None,
    max_concurrency: int = 5,
) -> list[TaskResult]:
    """Run tasks in parallel using asyncio.to_thread for synchronous graders.

    Each task is run in a separate thread via asyncio.to_thread(), allowing
    independent tasks to execute concurrently without blocking the event loop.
    A semaphore limits the number of concurrently running tasks.

    Args:
        tasks: List of Task objects to evaluate.
        outputs: Mapping of task_id to output dict. Missing entries default to {}.
        model_roles: Optional mapping of role name to model id, forwarded to
            graders that support model_role overrides (e.g. llm_judge).
        max_concurrency: Maximum number of tasks running simultaneously.
            Defaults to 5 to match typical LLM-judge API rate limits.

    Returns:
        List of TaskResult in the same order as the input tasks list.
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_one(task: Task) -> TaskResult:
        async with semaphore:
            output = outputs.get(task.task_id, {})
            return await asyncio.to_thread(
                _compute_task_result, task, output, model_roles=model_roles
            )

    return list(await asyncio.gather(*[_run_one(t) for t in tasks]))


async def run_eval_run_async(
    tasks: list[Task],
    outputs: dict[str, dict[str, Any]],
    *,
    layer: Layer | None = None,
    model_roles: dict[str, str] | None = None,
    max_concurrency: int = 5,
) -> EvalRun:
    """Run tasks in parallel and return a fully populated EvalRun.

    Convenience wrapper around run_suite_async() that constructs the EvalRun
    object with gate classification, matching the interface of the sync
    run_suite() in runner.py.

    Args:
        tasks: List of Task objects to evaluate.
        outputs: Mapping of task_id to output dict.
        layer: Optional layer enum for the run metadata.
        model_roles: Optional model role overrides.
        max_concurrency: Max parallel tasks. Defaults to 5.

    Returns:
        EvalRun with all TaskResults, scores, and gate classification populated.
    """
    run = EvalRun(
        run_id=str(uuid.uuid4()),
        layer=layer or Layer.PRODUCT,
        tasks_total=len(tasks),
    )
    if model_roles:
        run.metadata["model_roles"] = model_roles

    results = await run_suite_async(
        tasks, outputs, model_roles=model_roles, max_concurrency=max_concurrency
    )

    for result in results:
        run.task_results.append(result)
        if result.passed:
            run.tasks_passed += 1
        else:
            run.tasks_failed += 1

    run.finished_at = datetime.now(UTC)
    if run.task_results:
        run.overall_score = sum(tr.score for tr in run.task_results) / len(run.task_results)

    run.gate_result = classify_gate(run)

    return run
