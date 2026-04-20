"""Tests for golden_set_tags on TaskResult."""

from __future__ import annotations

import json

from gbr_eval.harness.models import EvalRun, GraderResult, Layer, TaskResult, Tier


def _make_grader_result() -> GraderResult:
    return GraderResult(grader_type="exact_match", passed=True, score=1.0)


class TestGoldenSetTags:
    def test_tags_field_exists_on_task_result(self):
        tr = TaskResult(
            task_id="test.tags",
            passed=True,
            score=1.0,
            grader_results=[_make_grader_result()],
            golden_set_tags=["seed", "regression"],
        )

        assert tr.golden_set_tags == ["seed", "regression"]

    def test_tags_in_json_report(self):
        tr = TaskResult(
            task_id="test.tags_json",
            passed=True,
            score=1.0,
            grader_results=[_make_grader_result()],
            golden_set_tags=["incident", "edge_case"],
        )
        run = EvalRun(
            run_id="run-tags",
            layer=Layer.PRODUCT,
            tier=Tier.GATE,
            task_results=[tr],
            tasks_total=1,
            tasks_passed=1,
        )

        data = json.loads(run.model_dump_json())

        assert data["task_results"][0]["golden_set_tags"] == ["incident", "edge_case"]

    def test_tags_null_when_not_set(self):
        tr = TaskResult(
            task_id="test.no_tags",
            passed=True,
            score=1.0,
            grader_results=[_make_grader_result()],
        )

        assert tr.golden_set_tags is None

        data = json.loads(tr.model_dump_json())
        assert data["golden_set_tags"] is None
