"""Tests for LLM engineering judge grader (engineering_judge.py).

All external API calls are mocked — these tests never hit the Anthropic API.
"""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import anthropic
import pytest

import gbr_eval.graders.engineering_judge  # noqa: F401 — trigger registration
from gbr_eval.graders._shared import _extract_json, _strip_markdown_fence
from gbr_eval.graders.engineering_judge import (
    EngineeringJudge,
    _truncate_code,
)
from gbr_eval.harness.models import GraderContext, GraderResult, GraderSpec


def _make_spec(
    field: str | None = None,
    weight: float = 1.0,
    required: bool = False,
    config: dict[str, Any] | None = None,
) -> GraderSpec:
    base_config = {"rubric": "Evaluate code quality."}
    if config:
        base_config.update(config)
    return GraderSpec(
        type="engineering_judge",
        field=field,
        weight=weight,
        required=required,
        config=base_config,
    )


def _make_api_response(
    score: int = 5,
    summary: str = "Clean code",
    findings: list[dict[str, str]] | None = None,
    escape_hatch: bool = False,
) -> MagicMock:
    from anthropic.types import TextBlock

    payload: dict[str, Any] = {
        "score": score,
        "summary": summary,
        "findings": findings or [],
        "escape_hatch_unknown": escape_hatch,
    }
    message = MagicMock()
    message.content = [TextBlock(type="text", text=json.dumps(payload))]
    return message


def _mock_grade(
    judge: EngineeringJudge,
    output: dict[str, Any],
    expected: dict[str, Any],
    spec: GraderSpec,
    api_response: MagicMock | None = None,
    side_effect: Exception | None = None,
    context: GraderContext | None = None,
) -> tuple[Any, MagicMock]:
    with (
        patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
        patch("anthropic.Anthropic") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        if side_effect:
            mock_client.messages.create.side_effect = side_effect
        else:
            mock_client.messages.create.return_value = api_response
        return judge.grade(output, expected, spec, context=context), mock_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestTruncateCode:
    def test_short_code_unchanged(self):
        code = "def foo(): pass"
        assert _truncate_code(code, max_chars=100) == code

    def test_long_code_truncated(self):
        code = "x" * 200
        result = _truncate_code(code, max_chars=50)
        assert len(result) < 200
        assert "truncated" in result

    def test_truncation_includes_total_length(self):
        code = "y" * 300
        result = _truncate_code(code, max_chars=100)
        assert "300 total" in result


class TestStripMarkdownFence:
    def test_no_fence_unchanged(self):
        text = '{"score": 5}'
        assert _strip_markdown_fence(text) == text

    def test_json_fence_stripped(self):
        text = '```json\n{"score": 5}\n```'
        assert _strip_markdown_fence(text) == '{"score": 5}'

    def test_plain_fence_stripped(self):
        text = '```\n{"score": 5}\n```'
        assert _strip_markdown_fence(text) == '{"score": 5}'


# ---------------------------------------------------------------------------
# Missing API key
# ---------------------------------------------------------------------------


class TestMissingApiKey:
    def test_returns_failed_result(self):
        spec = _make_spec()
        judge = EngineeringJudge()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge.grade({"content": "def foo(): pass"}, {}, spec)
        assert not result.passed
        assert "ANTHROPIC_API_KEY" in result.details

    def test_preserves_weight_and_field(self):
        spec = _make_spec(field="security", weight=2.0)
        judge = EngineeringJudge()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge.grade({"content": "x"}, {}, spec)
        assert result.weight == 2.0
        assert result.field == "security"


# ---------------------------------------------------------------------------
# Missing rubric
# ---------------------------------------------------------------------------


class TestMissingRubric:
    def test_error_when_no_rubric(self):
        spec = GraderSpec(
            type="engineering_judge",
            config={},
        )
        judge = EngineeringJudge()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = judge.grade({"content": "def foo(): pass"}, {}, spec)
        assert not result.passed
        assert result.error is not None
        assert "rubric" in result.error


# ---------------------------------------------------------------------------
# Empty file
# ---------------------------------------------------------------------------


class TestEmptyFile:
    def test_empty_file_skipped(self):
        spec = _make_spec()
        judge = EngineeringJudge()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = judge.grade({"content": ""}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "Empty file" in result.details

    def test_whitespace_only_skipped(self):
        spec = _make_spec()
        judge = EngineeringJudge()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = judge.grade({"content": "   \n\n  "}, {}, spec)
        assert result.passed


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------


class TestEngineeringJudgeGrade:
    def test_high_score_passes(self):
        spec = _make_spec(config={"min_score": 3.0})
        response = _make_api_response(score=5, summary="Excellent code")
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "def foo(): pass"}, {}, spec, response
        )
        assert result.passed
        assert result.score == pytest.approx(1.0)

    def test_low_score_fails(self):
        spec = _make_spec(config={"min_score": 3.0})
        response = _make_api_response(score=2, summary="Major issues")
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "def foo(): pass"}, {}, spec, response
        )
        assert not result.passed

    def test_score_normalization(self):
        spec = _make_spec(config={"min_score": 3.0})
        response = _make_api_response(score=3)
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x = 1"}, {}, spec, response
        )
        assert result.score == pytest.approx(0.5)

    def test_boundary_score_passes(self):
        spec = _make_spec(config={"min_score": 4.0})
        response = _make_api_response(score=4)
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x = 1"}, {}, spec, response
        )
        assert result.passed

    def test_grader_type_is_engineering_judge(self):
        spec = _make_spec()
        response = _make_api_response(score=5)
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert result.grader_type == "engineering_judge"

    def test_details_include_score_and_summary(self):
        spec = _make_spec()
        response = _make_api_response(score=4, summary="Mostly good")
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert "4.0/5" in result.details
        assert "Mostly good" in result.details

    def test_findings_in_details(self):
        spec = _make_spec()
        findings = [
            {"location": "foo()", "severity": "high", "issue": "Missing validation", "recommendation": "Add check"},
        ]
        response = _make_api_response(score=3, findings=findings)
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert "[high] foo()" in result.details
        assert "Missing validation" in result.details

    def test_many_findings_truncated(self):
        spec = _make_spec()
        findings = [
            {"location": f"fn{i}()", "severity": "low", "issue": f"Issue {i}", "recommendation": "Fix"}
            for i in range(8)
        ]
        response = _make_api_response(score=3, findings=findings)
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert "+3 more" in result.details

    def test_custom_model_used(self):
        spec = _make_spec(config={"model": "claude-haiku-4-5"})
        response = _make_api_response(score=5)
        _, mock_client = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5"

    def test_default_model_is_opus(self):
        spec = _make_spec()
        response = _make_api_response(score=5)
        _, mock_client = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-opus-4-20250514"


# ---------------------------------------------------------------------------
# Escape hatch
# ---------------------------------------------------------------------------


class TestEscapeHatch:
    def test_escape_hatch_passes_with_full_score(self):
        spec = _make_spec()
        response = _make_api_response(score=1, escape_hatch=True, summary="Config file, not reviewable")
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert result.passed
        assert result.score == 1.0
        assert "not applicable" in result.details

    def test_escape_hatch_includes_summary(self):
        spec = _make_spec()
        response = _make_api_response(escape_hatch=True, summary="Generated migration")
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert "Generated migration" in result.details


# ---------------------------------------------------------------------------
# Context (previous grader results)
# ---------------------------------------------------------------------------


class TestContextAwareness:
    def test_previous_results_in_prompt(self):
        spec = _make_spec()
        response = _make_api_response(score=5)
        prev = GraderResult(
            grader_type="pattern_required",
            field="tenant_check",
            passed=True,
            score=1.0,
            details="Pattern found",
        )
        ctx = GraderContext(metadata={}, previous_results=[prev])
        _, mock_client = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response, context=ctx
        )
        prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "Deterministic Grader Results" in prompt
        assert "pattern_required[tenant_check]: PASS" in prompt

    def test_model_role_override_from_context(self):
        spec = GraderSpec(
            type="engineering_judge",
            config={"rubric": "test"},
            model_role="reviewer",
        )
        ctx = GraderContext(
            metadata={"model_roles": {"reviewer": "claude-haiku-4-5"}},
            previous_results=[],
        )
        response = _make_api_response(score=5)
        _, mock_client = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response, context=ctx
        )
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5"


# ---------------------------------------------------------------------------
# API errors
# ---------------------------------------------------------------------------


class TestApiErrors:
    def test_timeout_returns_error(self):
        spec = _make_spec()
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec,
            side_effect=TimeoutError("timed out"),
        )
        assert not result.passed
        assert result.error is not None
        assert "TimeoutError" in result.error

    def test_invalid_json_returns_error(self):
        from anthropic.types import TextBlock
        spec = _make_spec()
        bad_message = MagicMock()
        bad_message.content = [TextBlock(type="text", text="not json {{{")]
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, bad_message
        )
        assert not result.passed
        assert result.error is not None

    def test_pii_sanitized_in_error(self):
        spec = _make_spec()
        exc = ValueError("failed for CPF 123.456.789-09")
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, side_effect=exc
        )
        assert result.error is not None
        assert "123.456.789-09" not in result.error

    def test_markdown_wrapped_json_parsed(self):
        from anthropic.types import TextBlock
        spec = _make_spec()
        wrapped = '```json\n{"score": 4, "summary": "Good", "findings": [], "escape_hatch_unknown": false}\n```'
        message = MagicMock()
        message.content = [TextBlock(type="text", text=wrapped)]
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, message
        )
        assert result.passed
        assert "4.0/5" in result.details


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------


def _make_rate_limit_error() -> anthropic.RateLimitError:
    import httpx
    req = httpx.Request("GET", "https://api.anthropic.com")
    resp = httpx.Response(429, request=req)
    return anthropic.RateLimitError("rate limited", response=resp, body=None)


class TestRetry:
    def test_retry_on_rate_limit(self):
        spec = _make_spec()
        success = _make_api_response(score=5)
        exc = _make_rate_limit_error()
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch("anthropic.Anthropic") as mock_cls,
            patch("gbr_eval.graders.engineering_judge.time.sleep"),
        ):
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [exc, success]
            result = EngineeringJudge().grade(
                {"content": "x"}, {}, spec
            )
        assert result.passed
        assert mock_client.messages.create.call_count == 2

    def test_max_retries_configurable(self):
        spec = _make_spec(config={"max_retries": 0})
        exc = _make_rate_limit_error()
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch("anthropic.Anthropic") as mock_cls,
            patch("gbr_eval.graders.engineering_judge.time.sleep"),
        ):
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = exc
            result = EngineeringJudge().grade(
                {"content": "x"}, {}, spec
            )
        assert not result.passed
        assert mock_client.messages.create.call_count == 1


# ---------------------------------------------------------------------------
# GraderStatus on error
# ---------------------------------------------------------------------------


class TestGraderStatusOnError:
    def test_api_error_sets_status_error(self):
        from gbr_eval.harness.models import GraderStatus

        spec = _make_spec()
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec,
            side_effect=TimeoutError("timed out"),
        )
        assert result.status == GraderStatus.ERROR

    def test_successful_grade_has_status_graded(self):
        from gbr_eval.harness.models import GraderStatus

        spec = _make_spec()
        response = _make_api_response(score=5)
        result, _ = _mock_grade(
            EngineeringJudge(), {"content": "x"}, {}, spec, response
        )
        assert result.status == GraderStatus.GRADED


# ---------------------------------------------------------------------------
# _extract_json
# ---------------------------------------------------------------------------


class TestExtractJson:
    def test_extract_json_plain(self):
        """Pure JSON passes through."""
        assert _extract_json('{"score": 5}') == '{"score": 5}'

    def test_extract_json_markdown_fence(self):
        """```json\\n{...}\\n``` extracts correctly."""
        text = '```json\n{"score": 5}\n```'
        result = _extract_json(text)
        assert '"score": 5' in result
        parsed = json.loads(result)
        assert parsed["score"] == 5

    def test_extract_json_prose_before(self):
        """'Here is my analysis:\\n{...}' extracts the JSON."""
        text = 'Here is my analysis:\n{"score": 5, "findings": []}'
        result = _extract_json(text)
        assert '"score": 5' in result
        parsed = json.loads(result)
        assert parsed["score"] == 5

    def test_extract_json_prose_after(self):
        """'{...}\\nNote: this is good' extracts the JSON."""
        text = '{"score": 5}\nNote: this is a good file'
        result = _extract_json(text)
        assert '"score": 5' in result
        parsed = json.loads(result)
        assert parsed["score"] == 5

    def test_extract_json_nested_braces(self):
        """Nested objects/arrays work."""
        text = '{"score": 5, "findings": [{"issue": "test", "nested": {"a": 1}}]}'
        result = _extract_json(text)
        parsed = json.loads(result)
        assert parsed["score"] == 5
        assert len(parsed["findings"]) == 1

    def test_extract_json_no_json(self):
        """No braces returns as-is (downstream will fail)."""
        text = "No JSON here at all"
        assert _extract_json(text) == text

    def test_extract_json_multiple_objects(self):
        """Only extracts the first top-level object."""
        text = '{"first": 1}\n{"second": 2}'
        result = _extract_json(text)
        parsed = json.loads(result)
        assert "first" in parsed
        assert "second" not in parsed
