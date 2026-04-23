"""Code Loader — loads source files from target repos for engineering graders."""

from __future__ import annotations

import time
import uuid
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from gbr_eval.graders.base import grade
from gbr_eval.harness.aggregator import aggregate_files_for_prompt
from gbr_eval.harness.cache import LLM_GRADER_TYPES, GraderCache
from gbr_eval.harness.models import (
    EvalRun,
    EvaluationMode,
    GraderContext,
    GraderResult,
    Layer,
    Task,
    TaskResult,
    Tier,
)
from gbr_eval.harness.regression import classify_gate
from gbr_eval.harness.runner import _compute_score, _resolve_git_sha, load_tasks_from_dir

if TYPE_CHECKING:
    from pathlib import Path

ProgressCallback = Callable[[str, int, int, float, bool], None]

_MAX_FILE_SIZE = 1_000_000  # 1 MB
_MAX_FILES = 10_000
_DEFAULT_EXCLUDE_DIRS = frozenset({
    "node_modules", ".next", "dist", "build", "__pycache__",
    ".git", ".venv", "venv", ".tox", "coverage", ".nyc_output",
})


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
        if any(part in _DEFAULT_EXCLUDE_DIRS for part in file_path.parts):
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


def evaluate_file(
    task: Task,
    file_path: str,
    content: str,
    *,
    cache: GraderCache | None = None,
) -> FileResult:
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
        ctx = GraderContext(metadata={}, previous_results=list(grader_results)) if grader_results else None

        # Cache lookup for LLM graders only.
        cached_result: GraderResult | None = None
        cache_key = ""
        if cache is not None and spec.type in LLM_GRADER_TYPES:
            cache_key = GraderCache.make_key(content, spec)
            cached_result = cache.get(cache_key)

        if cached_result is not None:
            cached_result.file_path = file_path
            grader_results.append(cached_result)
        else:
            result = grade(spec.type, output, task.expected, spec, context=ctx)
            result.file_path = file_path
            if cache is not None and spec.type in LLM_GRADER_TYPES and cache_key:
                cache.put(cache_key, result)
            grader_results.append(result)

    required_results = [r for r in grader_results if r.required]
    conforming = all(r.passed for r in required_results) if required_results else all(r.passed for r in grader_results)
    return FileResult(file_path=file_path, conforming=conforming, grader_results=grader_results)


def _resolve_changed_files(
    code_dir: Path,
    repo: str,
    *,
    changed_files: set[str] | None = None,
    base_branch: str | None = None,
) -> set[str] | None:
    """Resolve changed files for a specific repo.

    If *changed_files* is already provided, returns it directly.
    If *base_branch* is set, runs ``git diff`` inside ``code_dir/repo``.
    """
    if changed_files is not None:
        return changed_files
    if base_branch is None:
        return None
    from gbr_eval.harness.git_diff import get_changed_files

    repo_path = (code_dir / repo).resolve()
    if not repo_path.is_dir():
        return None
    try:
        return get_changed_files(repo_path, base_branch)
    except (RuntimeError, ValueError):
        return None


def run_task_holistic(
    task: Task,
    code_dir: Path,
    *,
    cache: GraderCache | None = None,
    changed_files: set[str] | None = None,
    base_branch: str | None = None,
) -> TaskResult:
    """Run a holistic task — aggregate files, grade once with LLM.

    Deterministic graders still run per-file (fast, per-file makes sense).
    LLM graders run once against the aggregated content.
    Score = LLM's normalized score (not conforming_files/total_files).
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
    resolved_changed = _resolve_changed_files(
        code_dir, repo, changed_files=changed_files, base_branch=base_branch,
    )
    if resolved_changed is not None:
        from gbr_eval.harness.git_diff import filter_changed_files
        files = filter_changed_files(files, resolved_changed)

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

    # Split graders into deterministic and LLM.
    det_specs = [s for s in task.graders if s.type not in LLM_GRADER_TYPES]
    llm_specs = [s for s in task.graders if s.type in LLM_GRADER_TYPES]

    # --- Stage 1: Run deterministic graders per-file ---
    det_results: list[GraderResult] = []
    for rel_path, content in files:
        for spec in det_specs:
            file_key = spec.config.get("file_key", "content")
            output: dict[str, Any] = {file_key: content}
            result = grade(spec.type, output, task.expected, spec)
            result.file_path = rel_path
            det_results.append(result)

    # --- Stage 2: Aggregate files and run LLM graders once ---
    llm_results: list[GraderResult] = []
    if llm_specs:
        aggregated = aggregate_files_for_prompt(files)

        # Build context with deterministic results for the LLM.
        ctx = GraderContext(metadata={}, previous_results=list(det_results)) if det_results else None

        for spec in llm_specs:
            file_key = spec.config.get("file_key", "content")
            output_dict: dict[str, Any] = {file_key: aggregated}

            cached_result: GraderResult | None = None
            cache_key = ""
            if cache is not None:
                cache_key = GraderCache.make_key(aggregated, spec)
                cached_result = cache.get(cache_key)

            if cached_result is not None:
                cached_result.file_path = "[holistic]"
                llm_results.append(cached_result)
            else:
                result = grade(spec.type, output_dict, task.expected, spec, context=ctx)
                result.file_path = "[holistic]"
                if cache is not None and cache_key:
                    cache.put(cache_key, result)
                llm_results.append(result)

    # --- Scoring ---
    all_results = det_results + llm_results
    duration_ms = (time.monotonic() - start) * 1000

    if llm_results and det_results:
        # Holistic combined: aggregate deterministic into one score, average with LLM.
        det_score = sum(1.0 for r in det_results if r.passed) / len(det_results)
        llm_score = sum(r.score * r.weight for r in llm_results) / sum(r.weight for r in llm_results)
        score = (det_score + llm_score) / 2.0
    elif llm_results:
        score = llm_results[0].score
    else:
        score = sum(1.0 for r in det_results if r.passed) / len(det_results) if det_results else 0.0

    # Required deterministic failure vetoes the holistic score.
    any_required_det_failed = any(r.required and not r.passed for r in det_results)
    any_required_llm_failed = any(r.required and not r.passed for r in llm_results)
    passed = score >= task.pass_threshold and not any_required_det_failed and not any_required_llm_failed

    return TaskResult(
        task_id=task.task_id,
        passed=passed,
        score=score,
        grader_results=all_results,
        duration_ms=duration_ms,
        pass_threshold=task.pass_threshold,
    )


def run_task_against_code(
    task: Task,
    code_dir: Path,
    *,
    cache: GraderCache | None = None,
    changed_files: set[str] | None = None,
    base_branch: str | None = None,
    use_funnel: bool = False,
    on_progress: ProgressCallback | None = None,
) -> TaskResult:
    """Run a task against actual code files from target repo.

    Dispatches to holistic mode when ``task.evaluation_mode`` is ``HOLISTIC``.
    Otherwise uses per-file mode where score = conforming_files / total_files.
    When *use_funnel* is True, routes per-file evaluation through the 3-stage
    grading funnel (deterministic → Haiku triage → Opus deep review).
    *on_progress* is called after each file: ``(file_path, idx, total, score, cached)``.
    """
    if task.evaluation_mode == EvaluationMode.HOLISTIC:
        return run_task_holistic(task, code_dir, cache=cache, changed_files=changed_files, base_branch=base_branch)

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
    resolved_changed = _resolve_changed_files(
        code_dir, repo, changed_files=changed_files, base_branch=base_branch,
    )
    if resolved_changed is not None:
        from gbr_eval.harness.git_diff import filter_changed_files
        files = filter_changed_files(files, resolved_changed)

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

    has_llm = any(s.type in LLM_GRADER_TYPES for s in task.graders)
    total = len(files)

    all_grader_results: list[GraderResult] = []
    conforming_count = 0
    if use_funnel and has_llm:
        from gbr_eval.harness.funnel import FunnelStats, run_file_through_funnel

        det_specs = [s for s in task.graders if s.type not in LLM_GRADER_TYPES]
        llm_specs = [s for s in task.graders if s.type in LLM_GRADER_TYPES]
        funnel_stats = FunnelStats()

        for idx, (rel_path, content) in enumerate(files, 1):
            fr = run_file_through_funnel(
                rel_path, content,
                det_specs=det_specs, llm_specs=llm_specs,
                expected=task.expected, cache=cache, stats=funnel_stats,
            )
            all_grader_results.extend(fr.grader_results)
            if fr.conforming:
                conforming_count += 1
            is_cached = any("[cached]" in r.details for r in fr.grader_results)
            if on_progress:
                on_progress(rel_path, idx, total, fr.grader_results[-1].score if fr.grader_results else 0.0, is_cached)
    else:
        for idx, (rel_path, content) in enumerate(files, 1):
            file_result = evaluate_file(task, rel_path, content, cache=cache)
            all_grader_results.extend(file_result.grader_results)
            if file_result.conforming:
                conforming_count += 1
            is_cached = any("[cached]" in r.details for r in file_result.grader_results)
            if on_progress:
                last_score = file_result.grader_results[-1].score if file_result.grader_results else 0.0
                on_progress(rel_path, idx, total, last_score, is_cached)

    duration_ms = (time.monotonic() - start) * 1000
    score = _compute_score(all_grader_results, task.scoring_mode)
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
    *,
    cache: GraderCache | None = None,
    changed_files: set[str] | None = None,
    base_branch: str | None = None,
    use_funnel: bool = False,
    on_progress: ProgressCallback | None = None,
) -> EvalRun:
    """Run engineering tasks against code from target repos.

    Defaults to Layer.ENGINEERING when no layer specified.
    """
    effective_layer = layer or Layer.ENGINEERING
    tasks = load_tasks_from_dir(tasks_dir, layer=effective_layer, tier=tier)

    repos: set[str] = {
        str(r) for t in tasks
        if (r := t.input.payload.get("repo")) and isinstance(r, str)
    }
    first_repo = sorted(repos)[0] if repos else None
    git_sha = _resolve_git_sha(code_dir, first_repo)

    run = EvalRun(
        run_id=str(uuid.uuid4()),
        layer=effective_layer,
        tier=tier,
        tasks_total=len(tasks),
        metadata={"code_dir": code_dir.name},
        git_sha=git_sha,
    )

    for task in tasks:
        result = run_task_against_code(
            task, code_dir, cache=cache, changed_files=changed_files,
            base_branch=base_branch, use_funnel=use_funnel, on_progress=on_progress,
        )
        run.task_results.append(result)
        if result.passed:
            run.tasks_passed += 1
        else:
            run.tasks_failed += 1

    run.finished_at = datetime.now(UTC)
    if run.task_results:
        run.overall_score = sum(tr.score for tr in run.task_results) / len(run.task_results)

    # Collect funnel stats from grader results.
    if use_funnel:
        skipped = sum(
            1 for tr in run.task_results
            for gr in tr.grader_results
            if "[funnel:skipped]" in gr.details
        )
        total_llm = sum(
            1 for tr in run.task_results
            for gr in tr.grader_results
            if gr.grader_type in LLM_GRADER_TYPES or "[funnel:skipped]" in gr.details
        )
        run.metadata["funnel_stats"] = {
            "total_llm_grader_results": total_llm,
            "funnel_skipped": skipped,
            "opus_reviewed": total_llm - skipped,
        }

    run.gate_result = classify_gate(run)

    return run
