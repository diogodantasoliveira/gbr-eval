"""Tests for the 3-stage grading funnel."""

from __future__ import annotations

from unittest.mock import patch

from gbr_eval.harness.funnel import FunnelStats, run_file_through_funnel
from gbr_eval.harness.models import GraderResult, GraderSpec, GraderStatus


def _det_spec(*, pattern: str = "eval\\(", forbidden: bool = True) -> GraderSpec:
    return GraderSpec(
        type="pattern_forbidden" if forbidden else "pattern_required",
        field="check",
        weight=1.0,
        required=True,
        config={"pattern": pattern, "file_key": "content"},
    )


def _llm_spec() -> GraderSpec:
    return GraderSpec(
        type="engineering_judge",
        field="review",
        weight=1.0,
        config={"rubric": "Check code quality", "file_key": "content", "min_score": 3.0},
    )


class TestStage1DeterministicFilter:
    def test_all_det_pass_no_llm_skips(self) -> None:
        """Files that pass all deterministic graders with no LLM specs → skip."""
        stats = FunnelStats()
        result = run_file_through_funnel(
            "clean.py", "print('hello')",
            det_specs=[_det_spec()], llm_specs=[],
            expected={}, stats=stats,
        )
        assert result.stage_reached == 1
        assert result.conforming is True
        assert stats.stage1_skipped == 1
        assert stats.stage3_reviewed == 0

    def test_det_fail_goes_to_stage3(self) -> None:
        """Required deterministic failure → straight to Stage 3 (Opus)."""
        stats = FunnelStats()

        def mock_grade(
            grader_type: str, output: dict, expected: dict, spec: GraderSpec, **kwargs: object
        ) -> GraderResult:
            if grader_type == "engineering_judge":
                return GraderResult(
                    grader_type="engineering_judge", field="review",
                    passed=False, score=0.25, weight=1.0,
                    details="score=2/5: bad code",
                )
            from gbr_eval.graders.base import grade
            return grade(grader_type, output, expected, spec, **kwargs)

        with patch("gbr_eval.harness.funnel.grade", side_effect=mock_grade):
            result = run_file_through_funnel(
                "bad.py", "eval('danger')",
                det_specs=[_det_spec()], llm_specs=[_llm_spec()],
                expected={}, stats=stats,
            )

        assert result.stage_reached == 3
        assert stats.stage3_reviewed == 1
        assert stats.stage1_skipped == 0


class TestStage2HaikuTriage:
    def test_triage_skip_no_review_needed(self) -> None:
        """Haiku says no review needed → skip Opus."""
        stats = FunnelStats()

        triage_result = GraderResult(
            grader_type="haiku_triage", field="triage",
            passed=True, score=1.0, weight=1.0,
            details="needs_review=False: config file",
        )

        call_count = {"grade": 0}

        def mock_grade(
            grader_type: str, output: dict, expected: dict, spec: GraderSpec, **kwargs: object
        ) -> GraderResult:
            call_count["grade"] += 1
            if grader_type == "haiku_triage":
                return triage_result
            if grader_type == "pattern_forbidden":
                from gbr_eval.graders.base import grade
                return grade(grader_type, output, expected, spec, **kwargs)
            raise AssertionError(f"Unexpected grader call: {grader_type}")

        with patch("gbr_eval.harness.funnel.grade", side_effect=mock_grade):
            result = run_file_through_funnel(
                "config.ts", "export default {}",
                det_specs=[_det_spec()], llm_specs=[_llm_spec()],
                expected={}, stats=stats,
            )

        assert result.stage_reached == 2
        assert stats.stage2_skipped == 1
        assert stats.stage3_reviewed == 0
        # LLM grader should have a SKIPPED result
        llm_results = [r for r in result.grader_results if r.grader_type == "engineering_judge"]
        assert len(llm_results) == 1
        assert llm_results[0].status == GraderStatus.SKIPPED
        assert "[funnel:skipped]" in llm_results[0].details

    def test_triage_sends_to_opus(self) -> None:
        """Haiku says needs review → Stage 3."""
        stats = FunnelStats()

        triage_result = GraderResult(
            grader_type="haiku_triage", field="triage",
            passed=False, score=0.0, weight=1.0,
            details="needs_review=True: has eval()",
        )
        opus_result = GraderResult(
            grader_type="engineering_judge", field="review",
            passed=False, score=0.25, weight=1.0,
            details="score=2/5: security issue",
        )

        def mock_grade(
            grader_type: str, output: dict, expected: dict, spec: GraderSpec, **kwargs: object
        ) -> GraderResult:
            if grader_type == "haiku_triage":
                return triage_result
            if grader_type == "engineering_judge":
                return opus_result
            from gbr_eval.graders.base import grade
            return grade(grader_type, output, expected, spec, **kwargs)

        with patch("gbr_eval.harness.funnel.grade", side_effect=mock_grade):
            result = run_file_through_funnel(
                "risky.ts", "export default {}",
                det_specs=[_det_spec()], llm_specs=[_llm_spec()],
                expected={}, stats=stats,
            )

        assert result.stage_reached == 3
        assert stats.stage3_reviewed == 1
        assert stats.stage2_skipped == 0


class TestFunnelStats:
    def test_opus_calls_saved(self) -> None:
        stats = FunnelStats(total_files=10, stage1_skipped=5, stage2_skipped=3, stage3_reviewed=2)
        assert stats.opus_calls_saved == 8
        assert abs(stats.skip_rate - 0.8) < 0.01

    def test_empty_stats(self) -> None:
        stats = FunnelStats()
        assert stats.opus_calls_saved == 0
        assert stats.skip_rate == 0.0


class TestFunnelWithCache:
    def test_stage3_uses_cache(self) -> None:
        """Stage 3 should check cache before calling Opus."""
        from gbr_eval.harness.cache import GraderCache

        triage_result = GraderResult(
            grader_type="haiku_triage", field="triage",
            passed=False, score=0.0, weight=1.0,
            details="needs review",
        )
        opus_result = GraderResult(
            grader_type="engineering_judge", field="review",
            passed=True, score=0.75, weight=1.0,
            details="score=4/5: good",
        )

        def mock_grade(
            grader_type: str, output: dict, expected: dict, spec: GraderSpec, **kwargs: object
        ) -> GraderResult:
            if grader_type == "haiku_triage":
                return triage_result
            if grader_type == "engineering_judge":
                return opus_result
            from gbr_eval.graders.base import grade
            return grade(grader_type, output, expected, spec, **kwargs)

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            cache = GraderCache(Path(td))
            llm_spec = _llm_spec()

            # First run — populates cache.
            with patch("gbr_eval.harness.funnel.grade", side_effect=mock_grade):
                run_file_through_funnel(
                    "file.ts", "code here",
                    det_specs=[_det_spec()], llm_specs=[llm_spec],
                    expected={}, cache=cache,
                )

            assert cache.stats.puts == 1
            assert cache.stats.misses == 1

            # Second run — should hit cache.
            with patch("gbr_eval.harness.funnel.grade", side_effect=mock_grade):
                result = run_file_through_funnel(
                    "file.ts", "code here",
                    det_specs=[_det_spec()], llm_specs=[llm_spec],
                    expected={}, cache=cache,
                )

            assert cache.stats.hits == 1
            eng_results = [r for r in result.grader_results if r.grader_type == "engineering_judge"]
            assert eng_results[0].details.startswith("[cached]")
