"""Code Loader — loads source files from target repos for engineering graders."""

from __future__ import annotations

import time
import uuid
import warnings
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.graders.base import grade
from gbr_eval.harness.models import (
    EvalRun,
    GraderResult,
    Layer,
    Task,
    TaskResult,
    Tier,
)
from gbr_eval.harness.regression import classify_gate
from gbr_eval.harness.runner import load_tasks_from_dir

_MAX_FILE_SIZE = 1_000_000  # 1 MB
_MAX_FILES = 10_000


@dataclass
class FileResult:
    """Result of evaluating a single file against a task's graders."""

    file_path: str
    conforming: bool
    grader_results: list[GraderResult] = field(default_factory=list)


def load_code_files(code_dir: Path, repo: str, scan_target: str) -> list[tuple[str, str]]:
    """Load source files from a target repo matching scan_target glob.

    Returns list of (relative_path, content) tuples.
    """
    if ".." in repo:
        return []

    repo_path = (code_dir / repo).resolve()
    if not repo_path.is_relative_to(code_dir.resolve()):
        return []
    if not repo_path.is_dir():
        return []

    if ".." in scan_target:
        return []

    files: list[tuple[str, str]] = []
    code_dir_resolved = code_dir.resolve()

    for file_path in sorted(repo_path.glob(scan_target)):
        if not file_path.is_file():
            continue
        resolved = file_path.resolve()
        if not resolved.is_relative_to(code_dir_resolved):
            continue
        try:
            if file_path.stat().st_size > _MAX_FILE_SIZE:
                continue
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel_path = str(file_path.relative_to(repo_path))
        files.append((rel_path, content))
        if len(files) >= _MAX_FILES:
            warnings.warn(
                f"File limit reached ({_MAX_FILES}). Narrow scan_target '{scan_target}'.",
                stacklevel=2,
            )
            break

    return files


def evaluate_file(task: Task, file_path: str, content: str) -> FileResult:
    """Evaluate a single file against all graders in a task."""
    if not task.graders:
        error_result = GraderResult(
            grader_type="system",
            passed=False,
            score=0.0,
            details="Task has no graders defined",
            file_path=file_path,
        )
        return FileResult(file_path=file_path, conforming=False, grader_results=[error_result])

    grader_results: list[GraderResult] = []
    for spec in task.graders:
        file_key = spec.config.get("file_key", "content")
        output: dict[str, Any] = {file_key: content}
        result = grade(spec.type, output, task.expected, spec)
        result.file_path = file_path
        grader_results.append(result)

    conforming = all(r.passed for r in grader_results)
    return FileResult(file_path=file_path, conforming=conforming, grader_results=grader_results)


def run_task_against_code(task: Task, code_dir: Path) -> TaskResult:
    """Run an engineering task against actual code files from target repo.

    Score = conforming_files / total_files
    """
    repo = task.input.payload.get("repo", "")
    scan_target = task.input.payload.get("scan_target", "**/*.py")

    if not repo:
        return TaskResult(
            task_id=task.task_id,
            passed=False,
            score=0.0,
            grader_results=[],
            duration_ms=0.0,
            pass_threshold=task.pass_threshold,
            error="Task missing input.payload.repo",
        )

    start = time.monotonic()
    files = load_code_files(code_dir, repo, scan_target)

    if not files:
        return TaskResult(
            task_id=task.task_id,
            passed=False,
            score=0.0,
            grader_results=[],
            duration_ms=(time.monotonic() - start) * 1000,
            pass_threshold=task.pass_threshold,
            error=f"No files found in repo '{repo}' with pattern '{scan_target}'",
        )

    all_grader_results: list[GraderResult] = []
    conforming_count = 0

    for rel_path, content in files:
        file_result = evaluate_file(task, rel_path, content)
        all_grader_results.extend(file_result.grader_results)
        if file_result.conforming:
            conforming_count += 1

    duration_ms = (time.monotonic() - start) * 1000
    score = conforming_count / len(files)
    any_required_failed = any(r.required and not r.passed for r in all_grader_results)
    passed = score >= task.pass_threshold and not any_required_failed

    return TaskResult(
        task_id=task.task_id,
        passed=passed,
        score=score,
        grader_results=all_grader_results,
        duration_ms=duration_ms,
        pass_threshold=task.pass_threshold,
    )


def run_engineering_suite(
    tasks_dir: Path,
    code_dir: Path,
    layer: Layer | None = None,
    tier: Tier | None = None,
) -> EvalRun:
    """Run engineering tasks against code from target repos.

    Defaults to Layer.ENGINEERING when no layer specified.
    """
    effective_layer = layer or Layer.ENGINEERING
    tasks = load_tasks_from_dir(tasks_dir, layer=effective_layer, tier=tier)

    run = EvalRun(
        run_id=str(uuid.uuid4()),
        layer=effective_layer,
        tier=tier,
        tasks_total=len(tasks),
        metadata={"code_dir": code_dir.name},
    )

    for task in tasks:
        result = run_task_against_code(task, code_dir)
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
