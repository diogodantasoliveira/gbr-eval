"""Tests for model roles (Pattern 2 from inspect_ai)."""

from __future__ import annotations

import sys
import warnings as _warnings_mod
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

import gbr_eval.graders  # noqa: F401

if TYPE_CHECKING:
    from pathlib import Path
from gbr_eval.graders.model_judge import _DEFAULT_MODEL, LLMJudge
from gbr_eval.harness.models import (
    Category,
    GraderContext,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.runner import _warn_unused_model_roles, run_task


def _make_task(**kwargs: object) -> Task:
    defaults: dict[str, object] = {
        "task_id": "test.roles",
        "category": Category.EXTRACTION,
        "component": "test",
        "layer": Layer.PRODUCT,
        "tier": Tier.GATE,
        "input": TaskInput(),
        "expected": {"cpf": "123.456.789-09"},
        "graders": [
            GraderSpec(type="exact_match", field="cpf", weight=1.0),
        ],
        "scoring_mode": ScoringMode.WEIGHTED,
        "pass_threshold": 0.95,
    }
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


# --- GraderSpec model_role ---


class TestGraderSpecModelRole:
    def test_default_is_none(self) -> None:
        spec = GraderSpec(type="exact_match", field="cpf")
        assert spec.model_role is None

    def test_model_role_from_dict(self) -> None:
        spec = GraderSpec(type="llm_judge", model_role="grader", config={"rubric": "test"})
        assert spec.model_role == "grader"

    def test_model_role_serialization_roundtrip(self) -> None:
        spec = GraderSpec(type="llm_judge", model_role="auditor", config={"rubric": "test"})
        data = spec.model_dump()
        restored = GraderSpec.model_validate(data)
        assert restored.model_role == "auditor"

    def test_model_role_in_yaml_loading(self, tmp_path: Path) -> None:
        yaml_content = """
task_id: test.role_yaml
category: extraction
component: test
layer: product
input: {}
graders:
  - type: llm_judge
    model_role: grader
    config:
      rubric: test
"""
        from gbr_eval.harness.runner import load_task

        task_file = tmp_path / "test.yaml"
        task_file.write_text(yaml_content)
        task = load_task(task_file)
        assert task.graders[0].model_role == "grader"


# --- LLM Judge role resolution ---


def _mock_anthropic_call(spec: GraderSpec, model_roles: dict[str, str] | None = None) -> str:
    """Run LLMJudge.grade with a mocked anthropic SDK, return the model used."""
    mock_text_block = MagicMock()
    mock_text_block.text = '{"score": 5, "reasoning": "ok", "escape_hatch_unknown": false}'

    mock_response = MagicMock()
    mock_response.content = [mock_text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client

    mock_types = MagicMock()
    mock_types.TextBlock = type(mock_text_block)

    ctx = GraderContext(metadata={"model_roles": model_roles} if model_roles else {})

    judge = LLMJudge()
    with (
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
        # Patch the module-level `anthropic` name in model_judge so that
        # `anthropic.Anthropic(...)` and `anthropic.APIError` use the mock.
        patch("gbr_eval.graders.model_judge.anthropic", mock_anthropic),
        # Patch sys.modules so the `from anthropic.types import TextBlock`
        # local import inside the try block resolves to the mock type.
        patch.dict(sys.modules, {"anthropic.types": mock_types}),
    ):
        judge.grade({}, {}, spec, context=ctx)

    return mock_client.messages.create.call_args.kwargs["model"]


class TestLLMJudgeRoleResolution:
    def test_role_mapping_used(self) -> None:
        spec = GraderSpec(
            type="llm_judge",
            model_role="grader",
            config={"rubric": "test"},
        )
        model = _mock_anthropic_call(spec, model_roles={"grader": "claude-haiku-3-5-20241022"})
        assert model == "claude-haiku-3-5-20241022"

    def test_fallback_to_config_model(self) -> None:
        spec = GraderSpec(
            type="llm_judge",
            model_role="grader",
            config={"rubric": "test", "model": "custom-model-123"},
        )
        assert _mock_anthropic_call(spec, model_roles={}) == "custom-model-123"

    def test_fallback_to_default_model(self) -> None:
        spec = GraderSpec(
            type="llm_judge",
            config={"rubric": "test"},
        )
        assert _mock_anthropic_call(spec) == _DEFAULT_MODEL

    def test_role_overrides_config_model(self) -> None:
        spec = GraderSpec(
            type="llm_judge",
            model_role="grader",
            config={"rubric": "test", "model": "should-be-overridden"},
        )
        assert _mock_anthropic_call(spec, model_roles={"grader": "role-wins"}) == "role-wins"


# --- run_task with model_roles ---


class TestRunTaskModelRoles:
    def test_deterministic_graders_ignore_roles(self) -> None:
        task = _make_task()
        output = {"cpf": "123.456.789-09"}
        result = run_task(task, output, model_roles={"grader": "some-model"})
        assert result.passed
        assert result.score == 1.0

    def test_run_task_without_roles_clean(self) -> None:
        task = _make_task()
        output = {"cpf": "123.456.789-09"}
        result = run_task(task, output)
        assert result.passed

    def test_roles_injected_in_spec_config(self) -> None:
        task = _make_task(
            graders=[
                GraderSpec(type="exact_match", field="cpf", model_role="grader"),
            ],
        )
        output = {"cpf": "123.456.789-09"}
        result = run_task(task, output, model_roles={"grader": "test-model"})
        assert result.passed

    def test_roles_not_injected_without_model_role(self) -> None:
        task = _make_task(
            graders=[
                GraderSpec(type="exact_match", field="cpf"),
            ],
        )
        output = {"cpf": "123.456.789-09"}
        result = run_task(task, output, model_roles={"grader": "test-model"})
        assert result.passed


# --- CLI --model-role parsing ---


class TestCLIModelRoleParsing:
    def test_single_role(self) -> None:
        from gbr_eval.harness.runner import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--model-role", "grader=claude-haiku", "--help"])
        assert result.exit_code == 0

    def test_invalid_format_raises(self, tmp_path: Path) -> None:
        from gbr_eval.harness.runner import cli

        yaml_content = """
task_id: test.cli_role
category: extraction
component: test
layer: product
input: {}
expected:
  cpf: "123"
graders:
  - type: exact_match
    field: cpf
"""
        task_file = tmp_path / "test.yaml"
        task_file.write_text(yaml_content)

        runner = CliRunner()
        result = runner.invoke(cli, [
            "run", "--task", str(task_file), "--model-role", "bad-format",
        ])
        assert result.exit_code != 0
        assert "Invalid --model-role format" in result.output


# --- Metadata traceability ---


class TestModelRolesMetadata:
    def test_roles_stored_in_run_suite_metadata(self, tmp_path: Path) -> None:
        from gbr_eval.harness.runner import run_suite

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        run = run_suite(tasks_dir, {}, model_roles={"grader": "test-model"})
        assert run.metadata["model_roles"] == {"grader": "test-model"}

    def test_no_roles_no_metadata_key(self, tmp_path: Path) -> None:
        from gbr_eval.harness.runner import run_suite

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        run = run_suite(tasks_dir, {})
        assert "model_roles" not in run.metadata


# --- _warn_unused_model_roles ---


class TestWarnUnusedModelRoles:
    def test_warn_unused_model_roles_warns(self) -> None:
        """Keys in model_roles that no grader references emit a UserWarning."""
        task = _make_task(
            graders=[GraderSpec(type="exact_match", field="cpf", weight=1.0)],
        )
        with pytest.warns(UserWarning, match="foo"):
            _warn_unused_model_roles([task], {"foo": "some-model"})

    def test_warn_unused_model_roles_no_warn_when_used(self) -> None:
        """A key that matches a grader's model_role must not produce a warning."""
        task = _make_task(
            graders=[
                GraderSpec(type="llm_judge", field="cpf", model_role="grader",
                           config={"rubric": "test"}),
            ],
        )
        with _warnings_mod.catch_warnings():
            _warnings_mod.simplefilter("error", UserWarning)
            # Should not raise — "grader" is used
            _warn_unused_model_roles([task], {"grader": "claude-sonnet-4-6"})

    def test_warn_unused_model_roles_partial_match(self) -> None:
        """Only the unused keys appear in the warning; used keys are silent."""
        task = _make_task(
            graders=[
                GraderSpec(type="llm_judge", field="cpf", model_role="grader",
                           config={"rubric": "test"}),
            ],
        )
        with pytest.warns(UserWarning, match="unused_key"):
            _warn_unused_model_roles(
                [task], {"grader": "claude-sonnet-4-6", "unused_key": "other-model"},
            )
