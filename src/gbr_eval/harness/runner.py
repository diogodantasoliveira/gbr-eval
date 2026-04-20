"""Eval harness runner — loads tasks, runs graders, produces results."""

from __future__ import annotations

import contextlib
import copy
import json as json_mod
import time
import uuid
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gbr_eval.harness.client import EvalClient, OutputRecorder

import click
import yaml

import gbr_eval.graders  # noqa: F401 — trigger auto-registration
from gbr_eval.graders.base import grade
from gbr_eval.harness.client import EvalClientError
from gbr_eval.harness.models import (
    Category,
    EvalRun,
    GateResult,
    GraderContext,
    GraderResult,
    GraderSpec,
    Layer,
    ScoreReducer,
    ScoringMode,
    Severity,
    Task,
    TaskInput,
    TaskResult,
    Tier,
)
from gbr_eval.harness.regression import RegressionDelta, classify_gate, compare_runs, load_baseline
from gbr_eval.harness.trends import detect_trends, load_runs_from_dir


def load_task(path: Path) -> Task:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    raw_graders = raw.get("graders", [])
    for g in raw_graders:
        if "config" in g and isinstance(g["config"], dict):
            g["config"] = {k: v for k, v in g["config"].items() if not k.startswith("_")}
    graders = [GraderSpec(**g) for g in raw_graders]
    task_input = TaskInput(**raw.get("input", {}))

    task = Task(
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
        target_threshold=raw.get("target_threshold"),
        baseline_run_id=raw.get("baseline_run_id"),
        regression_signal=raw.get("regression_signal"),
        eval_owner=raw.get("eval_owner"),
        eval_cadence=raw.get("eval_cadence"),
        golden_set_tags=raw.get("golden_set_tags"),
        epochs=int(raw.get("epochs", 1)),
        reducers=[ScoreReducer(r) for r in raw.get("reducers", ["mean"])],
        primary_reducer=ScoreReducer(raw.get("primary_reducer", "mean")),
    )

    if task.tier == Tier.GATE:
        if task.target_threshold is None:
            warnings.warn(f"Task {task.task_id}: no target_threshold set (EVAL First #5)", stacklevel=1)
        if task.regression_signal is None:
            warnings.warn(f"Task {task.task_id}: no regression_signal set (EVAL First #6)", stacklevel=1)
        if task.eval_owner is None:
            warnings.warn(f"Task {task.task_id}: no eval_owner set (EVAL First #7)", stacklevel=1)

    return task


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


_NON_DETERMINISTIC_GRADERS: frozenset[str] = frozenset({"llm_judge"})


def _all_graders_deterministic(task: Task) -> bool:
    return all(g.type not in _NON_DETERMINISTIC_GRADERS for g in task.graders)


def _reduce_scores(scores: list[float], reducer: ScoreReducer, threshold: float) -> float:
    if not scores:
        return 0.0
    if reducer == ScoreReducer.MEAN:
        return sum(scores) / len(scores)
    if reducer == ScoreReducer.MEDIAN:
        s = sorted(scores)
        n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    if reducer == ScoreReducer.AT_LEAST_ONE:
        return 1.0 if any(s >= threshold for s in scores) else max(scores)
    if reducer == ScoreReducer.ALL_PASS:
        return 1.0 if all(s >= threshold for s in scores) else min(scores)
    # MAJORITY
    passing = sum(1 for s in scores if s >= threshold)
    return 1.0 if passing > len(scores) / 2 else sum(scores) / len(scores)


def _run_single_epoch(
    task: Task,
    output: dict[str, Any],
    *,
    model_roles: dict[str, str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> tuple[list[GraderResult], float, float]:
    """Run all graders once. Returns (grader_results, score, duration_ms)."""
    start = time.monotonic()
    grader_results: list[GraderResult] = []
    metadata: dict[str, Any] = {"task_id": task.task_id, "tenant_profile": task.tenant_profile}
    if model_roles:
        metadata["model_roles"] = model_roles
    if extra_metadata:
        metadata.update(extra_metadata)
    ctx = GraderContext(metadata=metadata)

    for spec in task.graders:
        result = grade(spec.type, output, task.expected, spec, context=ctx)
        sev_raw = spec.config.get("severity")
        if sev_raw is not None:
            with contextlib.suppress(ValueError):
                result.severity = Severity(sev_raw)
        grader_results.append(result)
        ctx = ctx.model_copy(update={"previous_results": [*ctx.previous_results, result]})

    duration_ms = (time.monotonic() - start) * 1000
    score = _compute_score(grader_results, task.scoring_mode)
    return grader_results, score, duration_ms


def _compute_task_result(
    task: Task,
    output: dict[str, Any],
    *,
    model_roles: dict[str, str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
    extra_duration_ms: float = 0.0,
) -> TaskResult:
    """Run epochs, reduce scores, and construct a TaskResult.

    This is the shared computation core used by both the sync runner (run_task)
    and the async solver runner (async_runner.run_task_with_solver). Solver-specific
    concerns (invoking the solver, capturing trace metadata) stay in the caller.
    """
    effective_epochs = 1 if (task.epochs > 1 and _all_graders_deterministic(task)) else task.epochs

    epoch_scores: list[float] = []
    all_grader_results: list[GraderResult] = []
    total_duration = 0.0

    for _ in range(effective_epochs):
        grader_results, score, duration_ms = _run_single_epoch(
            task, output, model_roles=model_roles, extra_metadata=extra_metadata,
        )
        epoch_scores.append(score)
        all_grader_results.extend(grader_results)
        total_duration += duration_ms

    total_duration += extra_duration_ms

    reducer_scores = {
        r.value: _reduce_scores(epoch_scores, r, task.pass_threshold)
        for r in task.reducers
    }
    primary_score = reducer_scores[task.primary_reducer.value]
    any_required_failed = any(r.required and not r.passed for r in all_grader_results)
    passed = primary_score >= task.pass_threshold and not any_required_failed

    return TaskResult(
        task_id=task.task_id,
        passed=passed,
        score=primary_score,
        grader_results=all_grader_results,
        duration_ms=total_duration,
        pass_threshold=task.pass_threshold,
        reducer_scores=reducer_scores,
        epoch_scores=epoch_scores,
    )


def run_task(task: Task, output: dict[str, Any], *, model_roles: dict[str, str] | None = None) -> TaskResult:
    return _compute_task_result(task, output, model_roles=model_roles)


def _compute_score(results: list[Any], mode: ScoringMode) -> float:
    if not results:
        return 0.0

    if mode == ScoringMode.BINARY:
        return 1.0 if all(r.passed for r in results) else 0.0

    if mode == ScoringMode.WEIGHTED:
        total_weight: float = sum(r.weight for r in results)
        if total_weight == 0:
            return 0.0
        return float(sum(r.score * r.weight for r in results) / total_weight)

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
    return float(sum(r.score * r.weight for r in optional) / total_weight)


def load_golden_cases(golden_dir: Path, document_type: str, tags: list[str] | None = None) -> list[dict[str, Any]]:
    """Load all golden set cases for a document type.

    Args:
        golden_dir: Root directory containing golden set subdirectories.
        document_type: Subdirectory name (e.g. "matricula").
        tags: When set, only cases containing at least one of these tags are
            returned. When ``None``, all cases are loaded (backward compatible).
    """
    skill_dir = golden_dir / document_type
    if not skill_dir.is_dir():
        return []
    cases = []
    for f in sorted(skill_dir.glob("case_[0-9]*.json")):
        cases.append(json_mod.loads(f.read_text()))
    if tags:
        cases = [c for c in cases if any(t in c.get("tags", []) for t in tags)]
    for case in cases:
        if case.get("reviewed_by") is None and case.get("annotator") != "example":
            warnings.warn(
                f"Golden case {document_type}/case_{case.get('case_number', '?')} has reviewed_by=null",
                stacklevel=1,
            )
    return cases


def _extract_document_type(task: Task) -> str | None:
    """Extract document_type from task input payload, expected, or skill name."""
    if task.input.payload:
        doc_type = task.input.payload.get("document_type")
        if doc_type:
            return str(doc_type)
        skill = str(task.input.payload.get("skill", ""))
        parts = skill.rsplit("_v", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
    val = task.expected.get("document_type") if task.expected else None
    return str(val) if val else None


def _resolve_output(
    case: dict[str, Any],
    task: Task,
    *,
    self_eval: bool,
    client: EvalClient | None = None,
    recorder: OutputRecorder | None = None,
) -> dict[str, Any]:
    """Resolve output for a single case: self-eval, replay, HTTP, or empty."""
    from gbr_eval.harness.client import EvalClient, OutputRecorder

    case_number = case.get("case_number", 0)

    # Self-eval always wins (known-good path)
    if self_eval:
        output: dict[str, Any] = copy.deepcopy(case["expected_output"])
        if "citation" in case:
            output["citation"] = case["citation"]
        return output

    # Replay from recorder (when no client)
    if isinstance(recorder, OutputRecorder) and not isinstance(client, EvalClient):
        replayed = recorder.load(task.task_id, case_number)
        if replayed is not None:
            return replayed

    # Online eval via HTTP client
    if isinstance(client, EvalClient) and task.input.endpoint:
        payload = dict(task.input.payload)
        if "document_id" in case:
            payload["document_id"] = case["document_id"]
        payload["case_number"] = case_number
        output = client.call(task.input.endpoint, payload)
        if isinstance(recorder, OutputRecorder):
            recorder.save(task.task_id, case_number, output)
        return output

    warnings.warn(
        f"No output source for task {task.task_id}: no self_eval, no client, no recorder",
        stacklevel=2,
    )
    return {}


def run_task_against_golden_set(
    task: Task,
    cases: list[dict[str, Any]],
    self_eval: bool = False,
    client: EvalClient | None = None,
    recorder: OutputRecorder | None = None,
    model_roles: dict[str, str] | None = None,
) -> TaskResult:
    """Run a task against all cases in a golden set, aggregating scores."""
    if not cases:
        return TaskResult(
            task_id=task.task_id,
            passed=False,
            score=0.0,
            grader_results=[],
            duration_ms=0.0,
            pass_threshold=task.pass_threshold,
            error="No golden set cases found",
        )

    case_scores: list[float] = []
    all_grader_results = []
    total_duration = 0.0

    for case in cases:
        try:
            expected = case["expected_output"]
        except KeyError:
            error_result = GraderResult(
                grader_type="system",
                passed=False,
                score=0.0,
                weight=1.0,
                details=f"Golden case missing 'expected_output' key (case_number={case.get('case_number', '?')})",
            )
            all_grader_results.append(error_result)
            case_scores.append(0.0)
            continue
        try:
            output = _resolve_output(case, task, self_eval=self_eval, client=client, recorder=recorder)
        except (EvalClientError, OSError, json_mod.JSONDecodeError, ValueError, KeyError) as e:
            error_result = GraderResult(
                grader_type="system",
                passed=False,
                score=0.0,
                weight=1.0,
                details=f"Output resolution failed: {e}",
            )
            all_grader_results.append(error_result)
            case_scores.append(0.0)
            total_duration += 0.0
            continue
        case_task = task.model_copy(update={"expected": expected})
        result = run_task(case_task, output, model_roles=model_roles)
        case_scores.append(result.score)
        all_grader_results.extend(result.grader_results)
        total_duration += result.duration_ms

    avg_score = sum(case_scores) / len(case_scores)
    all_passed = all(s >= task.pass_threshold for s in case_scores)
    all_tags = sorted({t for c in cases for t in c.get("tags", [])})
    tags = all_tags if all_tags else None

    return TaskResult(
        task_id=task.task_id,
        passed=all_passed,
        score=avg_score,
        grader_results=all_grader_results,
        duration_ms=total_duration,
        pass_threshold=task.pass_threshold,
        golden_set_tags=tags,
    )


def run_suite(
    tasks_dir: Path,
    outputs: dict[str, dict[str, Any]],
    layer: Layer | None = None,
    tier: Tier | None = None,
    model_roles: dict[str, str] | None = None,
) -> EvalRun:
    tasks = load_tasks_from_dir(tasks_dir, layer=layer, tier=tier)
    run = EvalRun(
        run_id=str(uuid.uuid4()),
        layer=layer or Layer.PRODUCT,
        tier=tier,
        tasks_total=len(tasks),
    )
    if model_roles:
        run.metadata["model_roles"] = model_roles

    for task in tasks:
        output = outputs.get(task.task_id, {})
        result = run_task(task, output, model_roles=model_roles)
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


def run_suite_with_golden(
    tasks_dir: Path,
    golden_dir: Path,
    self_eval: bool = False,
    layer: Layer | None = None,
    tier: Tier | None = None,
    client: EvalClient | None = None,
    recorder: OutputRecorder | None = None,
    model_roles: dict[str, str] | None = None,
) -> EvalRun:
    """Run all tasks using golden set cases as reference data."""
    tasks = load_tasks_from_dir(tasks_dir, layer=layer, tier=tier)
    run = EvalRun(
        run_id=str(uuid.uuid4()),
        layer=layer or Layer.PRODUCT,
        tier=tier,
        tasks_total=len(tasks),
    )
    if model_roles:
        run.metadata["model_roles"] = model_roles

    for task in tasks:
        doc_type = _extract_document_type(task)
        cases = load_golden_cases(golden_dir, doc_type, tags=task.golden_set_tags) if doc_type else []
        if doc_type and not cases:
            warnings.warn(f"No golden set cases found for document type '{doc_type}'", stacklevel=1)
        if cases:
            result = run_task_against_golden_set(
                task, cases, self_eval=self_eval, client=client, recorder=recorder, model_roles=model_roles,
            )
        elif self_eval and task.expected:
            placeholder_fields = [k for k, v in task.expected.items() if isinstance(v, str) and "PLACEHOLDER" in v]
            if placeholder_fields:
                warnings.warn(
                    f"Task {task.task_id}: self-eval against PLACEHOLDER expected values "
                    f"({', '.join(placeholder_fields)}). Results may be tautological.",
                    stacklevel=1,
                )
            result = run_task(task, dict(task.expected), model_roles=model_roles)
        else:
            result = run_task(task, {}, model_roles=model_roles)

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


def _warn_unused_model_roles(tasks: list[Task], model_roles: dict[str, str]) -> None:
    used_roles = {spec.model_role for task in tasks for spec in task.graders if spec.model_role}
    unused = set(model_roles) - used_roles
    if unused:
        warnings.warn(
            f"--model-role keys not referenced by any grader's model_role: {sorted(unused)}",
            stacklevel=2,
        )


@click.group()
@click.version_option(version="0.1.0", prog_name="gbr-eval")
def cli() -> None:
    """gbr-eval — eval-first quality framework for GarantiaBR."""


def _parse_model_roles(model_role: tuple[str, ...]) -> dict[str, str] | None:
    """Parse --model-role key=value pairs into a dict.

    Returns None when no pairs are given, or the populated dict.
    Raises click.UsageError on invalid format.
    """
    if not model_role:
        return None
    model_roles: dict[str, str] = {}
    for pair in model_role:
        if "=" not in pair:
            raise click.UsageError(f"Invalid --model-role format: '{pair}' (expected role=model)")
        role, model_id = pair.split("=", 1)
        model_roles[role.strip()] = model_id.strip()
    return model_roles


def _setup_client_recorder(
    endpoint: str | None,
    allow_internal: bool,
    tenant: str,
    record_dir: Path | None,
    replay_dir: Path | None,
) -> tuple[Any, Any]:
    """Create EvalClient and/or OutputRecorder based on CLI flags.

    Returns (client, recorder) — either may be None when the flag was not set.
    """
    client = None
    recorder = None
    if endpoint or record_dir or replay_dir:
        from gbr_eval.harness.client import EvalClient, OutputRecorder
        if endpoint:
            client = EvalClient(
                base_url=endpoint,
                headers={"X-Tenant-ID": tenant},
                allow_internal=allow_internal,
            )
        if record_dir:
            recorder = OutputRecorder(record_dir=record_dir)
        elif replay_dir:
            recorder = OutputRecorder(record_dir=replay_dir)
    return client, recorder


def _run_code_eval(
    suite: Path | None,
    task_path: Path | None,
    code_dir: Path,
    layer_enum: Layer | None,
    tier_enum: Tier | None,
) -> EvalRun:
    """Handle --code-dir branch: engineering layer eval against a repo on disk."""
    from gbr_eval.harness.code_loader import run_engineering_suite, run_task_against_code

    if task_path:
        task = load_task(task_path)
        result = run_task_against_code(task, code_dir)
        return EvalRun(
            run_id=str(uuid.uuid4()),
            layer=task.layer,
            tier=task.tier,
            tasks_total=1,
            tasks_passed=1 if result.passed else 0,
            tasks_failed=0 if result.passed else 1,
            task_results=[result],
            overall_score=result.score,
            finished_at=datetime.now(UTC),
        )
    assert suite is not None
    return run_engineering_suite(suite, code_dir, layer=layer_enum, tier=tier_enum)


def _run_single_task_eval(
    task_path: Path,
    golden_dir: Path | None,
    self_eval: bool,
    client: Any,
    recorder: Any,
    model_roles: dict[str, str] | None,
) -> EvalRun:
    """Handle single --task branch (with or without --golden-dir)."""
    task = load_task(task_path)
    if model_roles:
        _warn_unused_model_roles([task], model_roles)
    if golden_dir:
        doc_type = _extract_document_type(task)
        cases = load_golden_cases(golden_dir, doc_type, tags=task.golden_set_tags) if doc_type else []
        if cases:
            result = run_task_against_golden_set(
                task, cases, self_eval=self_eval, client=client, recorder=recorder,
                model_roles=model_roles,
            )
        elif self_eval and task.expected:
            result = run_task(task, dict(task.expected), model_roles=model_roles)
        else:
            result = run_task(task, {}, model_roles=model_roles)
    else:
        result = run_task(task, {}, model_roles=model_roles)
    return EvalRun(
        run_id=str(uuid.uuid4()),
        layer=task.layer,
        tier=task.tier,
        tasks_total=1,
        tasks_passed=1 if result.passed else 0,
        tasks_failed=0 if result.passed else 1,
        task_results=[result],
        overall_score=result.score,
        finished_at=datetime.now(UTC),
    )


def _run_golden_suite_eval(
    suite: Path,
    golden_dir: Path,
    self_eval: bool,
    layer_enum: Layer | None,
    tier_enum: Tier | None,
    client: Any,
    recorder: Any,
    model_roles: dict[str, str] | None,
) -> EvalRun:
    """Handle --suite + --golden-dir branch."""
    if model_roles:
        _warn_unused_model_roles(load_tasks_from_dir(suite, layer=layer_enum, tier=tier_enum), model_roles)
    return run_suite_with_golden(
        suite, golden_dir, self_eval=self_eval, layer=layer_enum, tier=tier_enum,
        client=client, recorder=recorder, model_roles=model_roles,
    )


def _run_plain_suite_eval(
    suite: Path,
    layer_enum: Layer | None,
    tier_enum: Tier | None,
    model_roles: dict[str, str] | None,
) -> EvalRun:
    """Handle plain --suite branch (no golden dir, no code dir)."""
    if model_roles:
        _warn_unused_model_roles(load_tasks_from_dir(suite, layer=layer_enum, tier=tier_enum), model_roles)
    return run_suite(suite, {}, layer=layer_enum, tier=tier_enum, model_roles=model_roles)


def _finalize_and_report(
    eval_run: EvalRun,
    baseline_run: Path | None,
    output_format: str,
    output_file: Path | None,
) -> None:
    """Apply regression delta, classify gate, emit report, and set exit code."""
    from gbr_eval.harness.reporter import ci_summary, console_report, json_report

    delta: RegressionDelta | None = None
    if baseline_run:
        baseline = load_baseline(baseline_run)
        delta = compare_runs(baseline, eval_run)
        eval_run.baseline_run_id = baseline.run_id

    eval_run.gate_result = classify_gate(eval_run, delta)

    if output_format == "json":
        report = json_report(eval_run, output_path=output_file)
        click.echo(report)
    else:
        click.echo(console_report(eval_run, delta=delta))
        click.echo(ci_summary(eval_run))

    if eval_run.gate_result == GateResult.NO_GO:
        raise SystemExit(1)
    elif eval_run.gate_result == GateResult.NO_GO_ABSOLUTE:
        raise SystemExit(2)


@cli.command()
@click.option("--suite", type=click.Path(exists=True, path_type=Path), help="Directory containing task YAMLs")
@click.option("--task", "task_path", type=click.Path(exists=True, path_type=Path), help="Single task YAML file")
@click.option("--layer",
              type=click.Choice(["engineering", "product", "operational", "compliance"]),
              default=None, help="Filter by layer")
@click.option("--tier", type=click.Choice(["gate", "regression", "canary"]), default=None, help="Filter by tier")
@click.option("--output-format", type=click.Choice(["console", "json"]), default="console", help="Output format")
@click.option("--output-file", type=click.Path(path_type=Path), default=None, help="Write JSON report to file")
@click.option("--baseline-run", type=click.Path(exists=True, path_type=Path), default=None,
              help="Baseline run JSON for regression delta")
@click.option("--golden-dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Golden set directory (loads cases as reference per task)")
@click.option("--self-eval", is_flag=True, default=False,
              help="Self-eval mode: use golden set expected_output as both output and reference")
@click.option("--endpoint", default=None,
              help="Base URL for online eval (e.g. http://staging:8000)")
@click.option("--allow-internal", is_flag=True, default=False,
              help="Allow --endpoint to target internal/private IPs (dev only)")
@click.option("--record", "record_dir", type=click.Path(path_type=Path), default=None,
              help="Record outputs to directory for replay")
@click.option("--replay", "replay_dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Replay recorded outputs instead of HTTP calls")
@click.option("--tenant", default="global", help="Tenant ID for online eval (X-Tenant-ID header)")
@click.option("--code-dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Root directory containing target repos (for engineering layer eval)")
@click.option("--model-role", "model_role_pairs", multiple=True,
              help="Role=model mapping (repeatable, e.g. --model-role grader=claude-sonnet-4-6)")
@click.option("--parallel", is_flag=True, default=False,
              help="Run suite tasks in parallel using asyncio (max 5 concurrent tasks). "
                   "Only applies to --suite without --golden-dir or --code-dir.")
def run(
    suite: Path | None,
    task_path: Path | None,
    layer: str | None,
    tier: str | None,
    output_format: str,
    output_file: Path | None,
    baseline_run: Path | None,
    golden_dir: Path | None,
    self_eval: bool,
    endpoint: str | None,
    allow_internal: bool,
    record_dir: Path | None,
    replay_dir: Path | None,
    tenant: str,
    code_dir: Path | None,
    model_role_pairs: tuple[str, ...],
    parallel: bool,
) -> None:
    """Run eval tasks and report results."""
    model_roles = _parse_model_roles(model_role_pairs)

    if not suite and not task_path:
        raise click.UsageError("Provide --suite or --task")
    if self_eval and endpoint:
        raise click.UsageError("--self-eval and --endpoint are mutually exclusive")
    if code_dir and golden_dir:
        raise click.UsageError("--code-dir and --golden-dir are mutually exclusive")
    if parallel and (task_path or golden_dir or code_dir):
        raise click.UsageError("--parallel only applies to --suite without --golden-dir or --code-dir")

    client, recorder = _setup_client_recorder(endpoint, allow_internal, tenant, record_dir, replay_dir)

    layer_enum = Layer(layer) if layer else None
    tier_enum = Tier(tier) if tier else None

    if code_dir:
        eval_run = _run_code_eval(suite, task_path, code_dir, layer_enum, tier_enum)
    elif task_path:
        eval_run = _run_single_task_eval(task_path, golden_dir, self_eval, client, recorder, model_roles)
    elif golden_dir:
        assert suite is not None
        eval_run = _run_golden_suite_eval(
            suite, golden_dir, self_eval, layer_enum, tier_enum, client, recorder, model_roles
        )
    elif parallel:
        import asyncio

        from gbr_eval.harness.async_suite_runner import run_eval_run_async

        assert suite is not None
        tasks = load_tasks_from_dir(suite, layer=layer_enum, tier=tier_enum)
        if model_roles:
            _warn_unused_model_roles(tasks, model_roles)
        eval_run = asyncio.run(
            run_eval_run_async(tasks, {}, layer=layer_enum, model_roles=model_roles)
        )
    else:
        assert suite is not None
        eval_run = _run_plain_suite_eval(suite, layer_enum, tier_enum, model_roles)

    _finalize_and_report(eval_run, baseline_run, output_format, output_file)


@cli.command()
@click.option("--runs-dir", type=click.Path(exists=True, path_type=Path), required=True,
              help="Directory containing run JSON files")
@click.option("--min-consecutive", type=int, default=3, help="Minimum consecutive runs for trend detection")
@click.option("--output-format", type=click.Choice(["console", "json"]), default="console", help="Output format")
def trends(runs_dir: Path, min_consecutive: int, output_format: str) -> None:
    """Detect score trends across historical runs."""
    import json as json_mod

    runs = load_runs_from_dir(runs_dir)
    alerts = detect_trends(runs, min_consecutive=min_consecutive)

    if output_format == "json":
        data = {
            "analyzed_runs": len(runs),
            "min_consecutive": min_consecutive,
            "trend_alerts": [
                {
                    "task_id": a.task_id,
                    "metric": a.metric,
                    "direction": a.direction,
                    "consecutive_runs": a.consecutive_runs,
                    "current_value": a.current_value,
                    "threshold": a.threshold,
                    "distance_to_threshold": a.distance_to_threshold,
                }
                for a in alerts
            ],
        }
        click.echo(json_mod.dumps(data, indent=2))
    else:
        if not alerts:
            click.echo("No trend alerts detected.")
        else:
            click.echo(f"Trend alerts ({len(alerts)}):")
            for a in alerts:
                symbol = "↓" if a.direction == "declining" else "↑"
                click.echo(
                    f"  {symbol} {a.task_id}: {a.direction} for {a.consecutive_runs} runs "
                    f"(current={a.current_value:.3f}, threshold={a.threshold:.3f}, "
                    f"distance={a.distance_to_threshold:+.3f})"
                )


@cli.command()
@click.option("--runs-dir", type=click.Path(exists=True, path_type=Path), required=True,
              help="Directory containing run JSON files")
@click.option("--top", type=int, default=10, help="Number of top results to show")
@click.option("--output-format", type=click.Choice(["console", "json"]), default="console", help="Output format")
def analyze(runs_dir: Path, top: int, output_format: str) -> None:
    """Analyze eval runs — find weak tasks, failing fields, patterns."""
    import json as json_mod

    from gbr_eval.harness.analyzer import analysis_to_dict, analyze_runs, format_analysis

    runs = load_runs_from_dir(runs_dir)
    if not runs:
        click.echo("No runs found.")
        return

    report = analyze_runs(runs, top_n=top)

    if output_format == "json":
        click.echo(json_mod.dumps(analysis_to_dict(report), indent=2))
    else:
        click.echo(format_analysis(report))
