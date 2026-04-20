"""Tests for the eval harness runner."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import gbr_eval.graders.deterministic  # noqa: F401
from gbr_eval.harness.models import (
    Category,
    GraderResult,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.runner import (
    _compute_score,
    load_golden_cases,
    load_task,
    load_tasks_from_dir,
    run_suite,
    run_task,
    run_task_against_golden_set,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestRunTask:
    def _make_task(self, graders: list[GraderSpec], scoring_mode: ScoringMode = ScoringMode.WEIGHTED) -> Task:
        return Task(
            task_id="test.task",
            category=Category.EXTRACTION,
            component="test",
            layer=Layer.PRODUCT,
            tier=Tier.GATE,
            input=TaskInput(),
            expected={"cpf": "123.456.789-09", "nome": "João"},
            graders=graders,
            scoring_mode=scoring_mode,
            pass_threshold=0.95,
        )

    def test_all_pass(self):
        task = self._make_task([
            GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True),
            GraderSpec(type="exact_match", field="nome", weight=2.0),
        ])
        output = {"cpf": "123.456.789-09", "nome": "João"}
        result = run_task(task, output)
        assert result.passed
        assert result.score == 1.0
        assert len(result.grader_results) == 2

    def test_required_fails(self):
        task = self._make_task([
            GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True),
            GraderSpec(type="exact_match", field="nome", weight=2.0),
        ])
        output = {"cpf": "WRONG", "nome": "João"}
        result = run_task(task, output)
        assert not result.passed

    def test_weighted_scoring(self):
        task = self._make_task([
            GraderSpec(type="exact_match", field="cpf", weight=3.0),
            GraderSpec(type="exact_match", field="nome", weight=1.0),
        ])
        output = {"cpf": "123.456.789-09", "nome": "WRONG"}
        result = run_task(task, output)
        assert result.score == pytest.approx(0.75)

    def test_binary_scoring(self):
        task = self._make_task(
            [
                GraderSpec(type="exact_match", field="cpf"),
                GraderSpec(type="exact_match", field="nome"),
            ],
            scoring_mode=ScoringMode.BINARY,
        )
        output = {"cpf": "123.456.789-09", "nome": "WRONG"}
        result = run_task(task, output)
        assert result.score == 0.0

    def test_hybrid_scoring_required_fails(self):
        task = self._make_task(
            [
                GraderSpec(type="exact_match", field="cpf", required=True),
                GraderSpec(type="exact_match", field="nome"),
            ],
            scoring_mode=ScoringMode.HYBRID,
        )
        output = {"cpf": "WRONG", "nome": "João"}
        result = run_task(task, output)
        assert result.score == 0.0

    def test_unknown_grader_returns_error(self):
        task = self._make_task([
            GraderSpec(type="nonexistent_grader", field="cpf"),
        ])
        result = run_task(task, {"cpf": "123"})
        assert not result.passed
        assert result.grader_results[0].error is not None


class TestLoadTask:
    def test_load_yaml(self, tmp_path: Path):
        yaml_content = """
task_id: test.load
category: extraction
component: ai-engine
layer: product
tier: gate

input:
  endpoint: /api/v1/extract

expected:
  cpf: "123"

graders:
  - type: exact_match
    field: cpf
    weight: 3
    required: true

scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = tmp_path / "test.yaml"
        task_file.write_text(yaml_content)

        task = load_task(task_file)
        assert task.task_id == "test.load"
        assert task.layer == Layer.PRODUCT
        assert len(task.graders) == 1
        assert task.graders[0].required is True

    def test_load_yaml_with_golden_set_tags(self, tmp_path: Path):
        yaml_content = """
task_id: test.tags
category: extraction
component: ai-engine
layer: product
tier: gate

input:
  endpoint: /api/v1/extract

expected:
  cpf: "123"

graders:
  - type: exact_match
    field: cpf
    weight: 3
    required: true

golden_set_tags:
  - seed
  - pj_owner

scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = tmp_path / "test_tags.yaml"
        task_file.write_text(yaml_content)

        task = load_task(task_file)
        assert task.golden_set_tags == ["seed", "pj_owner"]

    def test_load_yaml_without_golden_set_tags(self, tmp_path: Path):
        yaml_content = """
task_id: test.no_tags
category: extraction
component: ai-engine
layer: product
tier: gate

input:
  endpoint: /api/v1/extract

expected:
  cpf: "123"

graders:
  - type: exact_match
    field: cpf
    weight: 3
    required: true

scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = tmp_path / "test_no_tags.yaml"
        task_file.write_text(yaml_content)

        task = load_task(task_file)
        assert task.golden_set_tags is None


_TASK_YAML = """\
task_id: {task_id}
category: extraction
component: ai-engine
layer: {layer}
tier: {tier}
input: {{}}
expected:
  field: value
graders:
  - type: exact_match
    field: field
    weight: 1.0
scoring_mode: weighted
pass_threshold: 0.95
"""


class TestLoadTasksFromDir:
    def _write_task(
        self, directory: Path, filename: str, task_id: str,
        layer: str = "product", tier: str = "gate",
    ) -> None:
        (directory / filename).write_text(
            _TASK_YAML.format(task_id=task_id, layer=layer, tier=tier)
        )

    def test_loads_all_yaml_files(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "a.yaml", "task.a")
        self._write_task(tmp_path, "b.yaml", "task.b")
        tasks = load_tasks_from_dir(tmp_path)
        assert {t.task_id for t in tasks} == {"task.a", "task.b"}

    def test_filters_by_layer(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "prod.yaml", "task.prod", layer="product")
        self._write_task(tmp_path, "eng.yaml", "task.eng", layer="engineering")
        tasks = load_tasks_from_dir(tmp_path, layer=Layer.PRODUCT)
        assert all(t.layer == Layer.PRODUCT for t in tasks)
        assert len(tasks) == 1

    def test_filters_by_tier(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "gate.yaml", "task.gate", tier="gate")
        self._write_task(tmp_path, "canary.yaml", "task.canary", tier="canary")
        tasks = load_tasks_from_dir(tmp_path, tier=Tier.CANARY)
        assert len(tasks) == 1
        assert tasks[0].tier == Tier.CANARY

    def test_returns_empty_for_empty_dir(self, tmp_path: Path) -> None:
        assert load_tasks_from_dir(tmp_path) == []


class TestComputeScore:
    def _result(self, passed: bool, score: float, weight: float = 1.0, required: bool = False) -> GraderResult:
        return GraderResult(
            grader_type="exact_match",
            passed=passed,
            score=score,
            weight=weight,
            required=required,
        )

    def test_weighted_zero_total_weight(self) -> None:
        results = [self._result(True, 1.0, weight=0.0)]
        assert _compute_score(results, ScoringMode.WEIGHTED) == 0.0

    def test_hybrid_all_required_pass_no_optional(self) -> None:
        results = [self._result(True, 1.0, required=True)]
        assert _compute_score(results, ScoringMode.HYBRID) == 1.0

    def test_hybrid_optional_only_zero_weight(self) -> None:
        results = [self._result(True, 1.0, weight=0.0, required=False)]
        assert _compute_score(results, ScoringMode.HYBRID) == 1.0

    def test_empty_results_returns_zero(self) -> None:
        assert _compute_score([], ScoringMode.WEIGHTED) == 0.0

    def test_binary_all_pass(self) -> None:
        results = [self._result(True, 1.0), self._result(True, 0.8)]
        assert _compute_score(results, ScoringMode.BINARY) == 1.0


class TestRunSuite:
    def _write_task(self, directory: Path, filename: str, task_id: str) -> None:
        (directory / filename).write_text(
            _TASK_YAML.format(task_id=task_id, layer="product", tier="gate")
        )

    def test_run_suite_all_pass(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "t1.yaml", "t1")
        run = run_suite(tmp_path, outputs={"t1": {"field": "value"}})
        assert run.tasks_total == 1
        assert run.tasks_passed == 1
        assert run.tasks_failed == 0
        assert run.overall_score == 1.0
        assert run.finished_at is not None

    def test_run_suite_task_fails(self, tmp_path: Path) -> None:
        self._write_task(tmp_path, "t1.yaml", "t1")
        run = run_suite(tmp_path, outputs={"t1": {"field": "wrong"}})
        assert run.tasks_failed == 1
        assert run.overall_score == 0.0

    def test_run_suite_empty_dir(self, tmp_path: Path) -> None:
        run = run_suite(tmp_path, outputs={})
        assert run.tasks_total == 0
        assert run.overall_score == 0.0

    def test_run_suite_filters_by_layer(self, tmp_path: Path) -> None:
        (tmp_path / "prod.yaml").write_text(_TASK_YAML.format(task_id="prod", layer="product", tier="gate"))
        (tmp_path / "eng.yaml").write_text(_TASK_YAML.format(task_id="eng", layer="engineering", tier="gate"))
        run = run_suite(tmp_path, outputs={}, layer=Layer.PRODUCT)
        assert run.tasks_total == 1


class TestLoadGoldenCasesTagFiltering:
    def _write_case(self, directory: Path, case_number: int, tags: list[str]) -> None:
        case = {
            "case_number": case_number,
            "tags": tags,
            "expected_output": {"field": "value"},
        }
        (directory / f"case_{case_number:03d}.json").write_text(json.dumps(case))

    def test_filter_by_seed_tag(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed"])
        self._write_case(doc_dir, 2, ["confuser"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=["seed"])
        assert len(cases) == 1
        assert cases[0]["tags"] == ["seed"]

    def test_filter_by_confuser_tag(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed"])
        self._write_case(doc_dir, 2, ["confuser"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=["confuser"])
        assert len(cases) == 1
        assert cases[0]["tags"] == ["confuser"]

    def test_no_filter_returns_all(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed"])
        self._write_case(doc_dir, 2, ["confuser"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=None)
        assert len(cases) == 2

    def test_multiple_tags_match_any(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed"])
        self._write_case(doc_dir, 2, ["confuser"])
        self._write_case(doc_dir, 3, ["edge_case"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=["seed", "edge_case"])
        assert len(cases) == 2
        assert {c["case_number"] for c in cases} == {1, 3}

    def test_case_with_multiple_tags_matches(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed", "pj_owner"])
        self._write_case(doc_dir, 2, ["confuser"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=["pj_owner"])
        assert len(cases) == 1
        assert cases[0]["case_number"] == 1

    def test_no_matching_tags_returns_empty(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=["nonexistent"])
        assert len(cases) == 0

    def test_case_without_tags_field_excluded_when_filtering(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        # Case with no tags field at all
        (doc_dir / "case_001.json").write_text(json.dumps({
            "case_number": 1,
            "expected_output": {"field": "value"},
        }))
        self._write_case(doc_dir, 2, ["seed"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=["seed"])
        assert len(cases) == 1
        assert cases[0]["case_number"] == 2

    def test_load_golden_cases_empty_tags_list_returns_all(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "test_doc"
        doc_dir.mkdir()
        self._write_case(doc_dir, 1, ["seed"])
        self._write_case(doc_dir, 2, ["confuser"])

        cases = load_golden_cases(tmp_path, "test_doc", tags=[])

        assert len(cases) == 2


class TestOverallScoreIsMeanOfTaskScores:
    """H1 fix: overall_score is mean of task scores, not pass-rate."""

    def test_overall_score_is_avg_not_pass_rate(self, tmp_path: Path) -> None:
        (tmp_path / "t1.yaml").write_text(_TASK_YAML.format(task_id="t1", layer="product", tier="gate"))
        (tmp_path / "t2.yaml").write_text(_TASK_YAML.format(task_id="t2", layer="product", tier="gate"))

        run = run_suite(tmp_path, outputs={"t1": {"field": "value"}, "t2": {"field": "wrong"}})

        assert run.tasks_passed == 1
        assert run.tasks_failed == 1
        assert run.overall_score == pytest.approx(0.5)


class TestTagsUnion:
    """H2 fix: golden_set_tags is union of all cases, not just first."""

    def test_tags_union_across_cases(self) -> None:
        task = Task(
            task_id="test.tags",
            category=Category.EXTRACTION,
            component="test",
            layer=Layer.PRODUCT,
            input=TaskInput(),
            graders=[GraderSpec(type="exact_match", field="f", weight=1.0)],
            expected={"f": "v"},
        )
        cases = [
            {"case_number": 1, "tags": ["seed", "pj"], "expected_output": {"f": "v"}},
            {"case_number": 2, "tags": ["seed", "sem_onus"], "expected_output": {"f": "v"}},
        ]

        result = run_task_against_golden_set(task, cases, self_eval=True)

        assert result.golden_set_tags is not None
        assert set(result.golden_set_tags) == {"seed", "pj", "sem_onus"}


class TestMissingExpectedOutputKey:
    """M fix: missing expected_output in case produces error, not crash."""

    def test_missing_expected_output_graceful(self) -> None:
        task = Task(
            task_id="test.missing",
            category=Category.EXTRACTION,
            component="test",
            layer=Layer.PRODUCT,
            input=TaskInput(),
            graders=[GraderSpec(type="exact_match", field="f", weight=1.0)],
            expected={"f": "v"},
        )
        cases = [
            {"case_number": 1, "tags": ["seed"]},
        ]

        result = run_task_against_golden_set(task, cases, self_eval=True)

        assert not result.passed
        assert result.score == 0.0
        assert any("expected_output" in gr.details for gr in result.grader_results)


class TestLoadTaskStripsPrivateConfigKeys:
    def test_underscore_keys_stripped_from_grader_config(self, tmp_path: Path) -> None:
        yaml_content = """\
task_id: test.strip_private
category: extraction
component: ai-engine
layer: product
tier: gate
input: {}
expected:
  field: value
graders:
  - type: exact_match
    field: field
    weight: 1.0
    config:
      _model_roles:
        grader: claude-sonnet-4-6
      severity: warning
scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = tmp_path / "test_strip.yaml"
        task_file.write_text(yaml_content)

        task = load_task(task_file)

        assert "_model_roles" not in task.graders[0].config
        assert task.graders[0].config.get("severity") == "warning"


class TestTargetThresholdValidation:
    """M fix: target_threshold has constraints and must be >= pass_threshold."""

    def test_target_below_pass_raises(self) -> None:
        with pytest.raises(ValueError, match="target_threshold"):
            Task(
                task_id="test.invalid",
                category=Category.EXTRACTION,
                component="test",
                layer=Layer.PRODUCT,
                input=TaskInput(),
                graders=[GraderSpec(type="exact_match", field="f")],
                pass_threshold=0.95,
                target_threshold=0.80,
            )

    def test_target_above_pass_valid(self) -> None:
        task = Task(
            task_id="test.valid",
            category=Category.EXTRACTION,
            component="test",
            layer=Layer.PRODUCT,
            input=TaskInput(),
            graders=[GraderSpec(type="exact_match", field="f")],
            pass_threshold=0.90,
            target_threshold=0.98,
        )
        assert task.target_threshold == 0.98

    def test_target_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            Task(
                task_id="test.range",
                category=Category.EXTRACTION,
                component="test",
                layer=Layer.PRODUCT,
                input=TaskInput(),
                graders=[GraderSpec(type="exact_match", field="f")],
                target_threshold=1.5,
            )
