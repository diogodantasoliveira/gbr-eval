"""3-Stage Grading Funnel — reduces Opus API calls by 80-95%.

Stage 1 (Deterministic): Run pattern graders.
  - All pass + no LLM relevance → SKIP (no LLM call)
  - Any required fail → Stage 3 directly (Opus needs failure context)
  - Pass but relevant → Stage 2

Stage 2 (Haiku Triage): Fast binary filter.
  - needs_deep_review=false → SKIP
  - needs_deep_review=true → Stage 3

Stage 3 (Opus Deep Review): Full engineering_judge with cache.

Only applies to ``per_file`` evaluation mode.  ``holistic`` mode already
makes a single LLM call — no funnel needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gbr_eval.graders.base import grade
from gbr_eval.harness.cache import GraderCache
from gbr_eval.harness.models import GraderContext, GraderResult, GraderSpec, GraderStatus


@dataclass
class FunnelStats:
    total_files: int = 0
    stage1_skipped: int = 0
    stage2_skipped: int = 0
    stage3_reviewed: int = 0
    stage2_errors: int = 0

    @property
    def opus_calls_saved(self) -> int:
        return self.stage1_skipped + self.stage2_skipped

    @property
    def skip_rate(self) -> float:
        return self.opus_calls_saved / self.total_files if self.total_files > 0 else 0.0


@dataclass
class FunnelResult:
    """Result of running a single file through the funnel."""

    file_path: str
    grader_results: list[GraderResult] = field(default_factory=list)
    stage_reached: int = 0
    conforming: bool = True


def run_file_through_funnel(
    file_path: str,
    content: str,
    *,
    det_specs: list[GraderSpec],
    llm_specs: list[GraderSpec],
    expected: dict[str, Any],
    cache: GraderCache | None = None,
    stats: FunnelStats | None = None,
) -> FunnelResult:
    """Run a single file through the 3-stage funnel.

    Args:
        file_path: Relative path of the file being evaluated.
        content: File content.
        det_specs: Deterministic grader specs (pattern_required, pattern_forbidden, etc.).
        llm_specs: LLM grader specs (engineering_judge).
        expected: Task expected dict.
        cache: Optional grader cache for Stage 3.
        stats: Optional stats tracker (mutated in-place).
    """
    result = FunnelResult(file_path=file_path)
    if stats:
        stats.total_files += 1

    # --- Stage 1: Deterministic pre-filter ---
    result.stage_reached = 1
    det_results: list[GraderResult] = []
    for spec in det_specs:
        file_key = spec.config.get("file_key", "content")
        output: dict[str, Any] = {file_key: content}
        ctx = GraderContext(metadata={}, previous_results=list(det_results)) if det_results else None
        gr = grade(spec.type, output, expected, spec, context=ctx)
        gr.file_path = file_path
        det_results.append(gr)

    result.grader_results.extend(det_results)

    any_required_failed = any(r.required and not r.passed for r in det_results)
    any_failed = any(not r.passed for r in det_results)

    if any_required_failed:
        # Required failure → go straight to Opus (needs failure context).
        pass  # fall through to Stage 3
    elif not any_failed and not llm_specs:
        # All pass, no LLM graders → done.
        if stats:
            stats.stage1_skipped += 1
        result.conforming = all(r.passed for r in result.grader_results)
        return result
    elif not any_failed:
        # All deterministic pass → Stage 2 triage.
        result.stage_reached = 2

        triage_rubric = _extract_rubric(llm_specs)
        if triage_rubric:
            triage_spec = GraderSpec(
                type="haiku_triage",
                field="triage",
                config={"rubric": triage_rubric, "file_key": "content"},
            )
            triage_output: dict[str, Any] = {"content": content}
            triage_result = grade("haiku_triage", triage_output, expected, triage_spec)
            triage_result.file_path = file_path

            if triage_result.passed:
                # Haiku says no deep review needed → skip Opus.
                for llm_spec in llm_specs:
                    skip_result = GraderResult(
                        grader_type=llm_spec.type,
                        field=llm_spec.field,
                        passed=True,
                        score=1.0,
                        weight=llm_spec.weight,
                        details="[funnel:skipped] Haiku triage: no deep review needed",
                        file_path=file_path,
                        status=GraderStatus.SKIPPED,
                    )
                    result.grader_results.append(skip_result)

                if stats:
                    stats.stage2_skipped += 1
                result.conforming = all(r.passed for r in result.grader_results)
                return result

            if triage_result.status == GraderStatus.ERROR and stats:
                stats.stage2_errors += 1
            # Fall through to Stage 3.

    # --- Stage 3: Opus deep review ---
    result.stage_reached = 3
    if stats:
        stats.stage3_reviewed += 1

    ctx = GraderContext(metadata={}, previous_results=list(det_results)) if det_results else None
    for spec in llm_specs:
        file_key = spec.config.get("file_key", "content")
        output = {file_key: content}

        cached: GraderResult | None = None
        cache_key = ""
        if cache is not None:
            cache_key = GraderCache.make_key(content, spec)
            cached = cache.get(cache_key)

        if cached is not None:
            cached.file_path = file_path
            result.grader_results.append(cached)
        else:
            gr = grade(spec.type, output, expected, spec, context=ctx)
            gr.file_path = file_path
            if cache is not None and cache_key:
                cache.put(cache_key, gr)
            result.grader_results.append(gr)

    result.conforming = all(r.passed for r in result.grader_results)
    return result


def _extract_rubric(llm_specs: list[GraderSpec]) -> str:
    """Extract the rubric from the first LLM spec for triage."""
    for spec in llm_specs:
        rubric = spec.config.get("rubric", "")
        if rubric:
            return str(rubric)
    return ""
