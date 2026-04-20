"""Utilities for composing and overriding tasks."""

from __future__ import annotations

from typing import Any

from gbr_eval.harness.models import Task


def task_with(task: Task, **overrides: Any) -> Task:
    """Clone a task with field overrides, running Pydantic validation on the result."""
    data = task.model_dump()
    data.update(overrides)
    return Task.model_validate(data)
