"""Tests for EVAL First validation warnings and new optional fields."""

from __future__ import annotations

import json
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.runner import load_task


def _write_task_yaml(tmp_path: Path, content: str) -> Path:
    task_file = tmp_path / "task.yaml"
    task_file.write_text(content)
    return task_file


class TestNewFieldsOptionalInYaml:
    def test_loads_without_optional_fields(self, tmp_path):
        yaml_content = """\
task_id: test.minimal
category: extraction
component: ai-engine
layer: product
tier: gate
input:
  endpoint: /api/v1/extract
expected:
  cpf: "123.456.789-00"
graders:
  - type: exact_match
    field: cpf
    weight: 1.0
scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = _write_task_yaml(tmp_path, yaml_content)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            task = load_task(task_file)

        assert task.target_threshold is None
        assert task.baseline_run_id is None
        assert task.regression_signal is None
        assert task.eval_owner is None
        assert task.eval_cadence is None

    def test_loads_with_all_optional_fields(self, tmp_path):
        yaml_content = """\
task_id: test.full
category: extraction
component: ai-engine
layer: product
tier: gate
input:
  endpoint: /api/v1/extract
expected:
  cpf: "123.456.789-00"
graders:
  - type: exact_match
    field: cpf
    weight: 1.0
scoring_mode: weighted
pass_threshold: 0.95
target_threshold: 0.99
baseline_run_id: run-abc123
regression_signal: score_drop_5pct
eval_owner: diogo@garantiabr.com
eval_cadence: daily
"""
        task_file = _write_task_yaml(tmp_path, yaml_content)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            task = load_task(task_file)

        assert task.target_threshold == 0.99
        assert task.baseline_run_id == "run-abc123"
        assert task.regression_signal == "score_drop_5pct"
        assert task.eval_owner == "diogo@garantiabr.com"
        assert task.eval_cadence == "daily"


class TestTargetThresholdInJsonReport:
    def test_target_threshold_serialized(self):
        task = Task(
            task_id="test.threshold",
            category=Category.EXTRACTION,
            component="ai-engine",
            layer=Layer.PRODUCT,
            tier=Tier.GATE,
            input=TaskInput(endpoint="/api/v1/extract"),
            expected={"cpf": "123"},
            graders=[GraderSpec(type="exact_match", field="cpf")],
            target_threshold=0.99,
        )

        data = json.loads(task.model_dump_json())

        assert data["target_threshold"] == 0.99

    def test_target_threshold_null_when_unset(self):
        task = Task(
            task_id="test.no_threshold",
            category=Category.EXTRACTION,
            component="ai-engine",
            layer=Layer.PRODUCT,
            input=TaskInput(),
            graders=[GraderSpec(type="exact_match")],
        )

        data = json.loads(task.model_dump_json())

        assert data["target_threshold"] is None


class TestEvalFirstWarnings:
    def test_warns_when_target_threshold_missing(self, tmp_path):
        yaml_content = """\
task_id: test.warn
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
scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = _write_task_yaml(tmp_path, yaml_content)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_task(task_file)

        threshold_warnings = [x for x in w if "target_threshold" in str(x.message)]
        assert len(threshold_warnings) == 1

    def test_warns_when_eval_owner_missing(self, tmp_path):
        yaml_content = """\
task_id: test.no_owner
category: classification
component: ai-engine
layer: product
tier: gate
input:
  endpoint: /api/v1/classify
expected:
  document_type: matricula
graders:
  - type: exact_match
    field: document_type
scoring_mode: binary
pass_threshold: 1.0
"""
        task_file = _write_task_yaml(tmp_path, yaml_content)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_task(task_file)

        owner_warnings = [x for x in w if "eval_owner" in str(x.message)]
        assert len(owner_warnings) == 1

    def test_no_warning_for_non_gate_tier(self, tmp_path):
        yaml_content = """\
task_id: test.regression
category: extraction
component: ai-engine
layer: product
tier: regression
input:
  endpoint: /api/v1/extract
expected:
  cpf: "123"
graders:
  - type: exact_match
    field: cpf
scoring_mode: weighted
pass_threshold: 0.95
"""
        task_file = _write_task_yaml(tmp_path, yaml_content)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_task(task_file)

        eval_first_warnings = [x for x in w if "EVAL First" in str(x.message)]
        assert eval_first_warnings == []
