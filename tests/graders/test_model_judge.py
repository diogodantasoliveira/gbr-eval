"""Tests for LLM-as-judge grader (model_judge.py).

All external API calls are mocked — these tests never hit the Anthropic API.
"""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import anthropic
import pytest

import gbr_eval.graders.model_judge  # noqa: F401 — trigger registration
from gbr_eval.graders.model_judge import LLMJudge, _sanitize_pii, _sanitize_pii_str
from gbr_eval.harness.models import GraderSpec


def _make_spec(
    field: str | None = None,
    weight: float = 1.0,
    required: bool = False,
    config: dict[str, Any] | None = None,
) -> GraderSpec:
    return GraderSpec(
        type="llm_judge",
        field=field,
        weight=weight,
        required=required,
        config=config or {},
    )


def _make_api_response(score: int = 5, reasoning: str = "Correct", escape_hatch: bool = False) -> MagicMock:
    """Build a mock Anthropic API response using real TextBlock for isinstance checks."""
    from anthropic.types import TextBlock

    payload = {"score": score, "reasoning": reasoning, "escape_hatch_unknown": escape_hatch}
    message = MagicMock()
    message.content = [TextBlock(type="text", text=json.dumps(payload))]
    return message


def _mock_grade(
    judge: LLMJudge,
    output: dict[str, Any],
    expected: dict[str, Any],
    spec: GraderSpec,
    api_response: MagicMock | None = None,
    side_effect: Exception | None = None,
) -> tuple[Any, MagicMock]:
    mock_client = MagicMock()
    if side_effect:
        mock_client.messages.create.side_effect = side_effect
    else:
        mock_client.messages.create.return_value = api_response
    with (
        patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
        patch("gbr_eval.graders.model_judge.get_anthropic_client", return_value=mock_client),
    ):
        return judge.grade(output, expected, spec), mock_client


class TestSanitizePii:
    def test_redacts_cpf(self):
        data = {"cpf": "123.456.789-09"}
        result = _sanitize_pii(data)
        assert "123.456.789" not in json.dumps(result)
        assert "000.000.000-XX" in json.dumps(result)

    def test_redacts_cnpj(self):
        data = {"cnpj": "12.345.678/0001-90"}
        result = _sanitize_pii(data)
        assert "12.345.678" not in json.dumps(result)
        assert "00.000.000/0000-XX" in json.dumps(result)

    def test_preserves_other_fields(self):
        data = {"nome": "João Silva", "area": 150.0}
        result = _sanitize_pii(data)
        assert result["nome"] == "João Silva"
        assert result["area"] == 150.0

    def test_returns_dict(self):
        data = {"key": "value"}
        result = _sanitize_pii(data)
        assert isinstance(result, dict)

    def test_multiple_pii_in_same_dict(self):
        data = {"cpf": "111.222.333-44", "cnpj": "98.765.432/0001-10"}
        result = _sanitize_pii(data)
        dumped = json.dumps(result)
        assert "111.222.333" not in dumped
        assert "98.765.432" not in dumped

    def test_no_pii_passes_through_unchanged(self):
        data = {"status": "aprovado", "score": 0.95}
        result = _sanitize_pii(data)
        assert result == data

    def test_redacts_unformatted_cpf(self):
        data = {"cpf_raw": "12345678909"}
        result = _sanitize_pii(data)
        assert "12345678909" not in json.dumps(result)

    def test_redacts_unformatted_cnpj(self):
        data = {"cnpj_raw": "12345678000190"}
        result = _sanitize_pii(data)
        assert "12345678000190" not in json.dumps(result)

    def test_redacts_cep(self):
        data = {"cep": "01310-100"}
        result = _sanitize_pii(data)
        assert "01310-100" not in json.dumps(result)

    def test_nested_dict_pii_redacted(self):
        data = {"person": {"cpf": "123.456.789-09", "name": "João"}}
        result = _sanitize_pii(data)
        assert "123.456.789" not in json.dumps(result)
        assert result["person"]["name"] == "João"

    def test_nested_list_pii_redacted(self):
        data = {"items": [{"cpf": "111.222.333-44"}, {"cpf": "555.666.777-88"}]}
        result = _sanitize_pii(data)
        dumped = json.dumps(result)
        assert "111.222.333" not in dumped
        assert "555.666.777" not in dumped


class TestSanitizePiiNewPatterns:
    def test_redacts_rg(self):
        data = {"rg": "1.234.567-8"}
        result = _sanitize_pii(data)
        assert "1.234.567" not in json.dumps(result)
        assert "0.000.000-X" in json.dumps(result)

    def test_redacts_rg_two_digit_prefix(self):
        data = {"rg": "12.345.678-X"}
        result = _sanitize_pii(data)
        assert "12.345.678" not in json.dumps(result)
        assert "0.000.000-X" in json.dumps(result)

    def test_redacts_pis_pasep(self):
        data = {"pis": "123.45678.90-1"}
        result = _sanitize_pii(data)
        assert "123.45678" not in json.dumps(result)
        assert "000.00000.00-0" in json.dumps(result)

    def test_rg_pattern_does_not_match_cpf(self):
        data = {"cpf": "123.456.789-09"}
        result = _sanitize_pii(data)
        assert "000.000.000-XX" in json.dumps(result)


class TestSanitizePiiStr:
    def test_redacts_cpf_in_plain_string(self):
        text = "CPF do cliente: 123.456.789-09"
        result = _sanitize_pii_str(text)
        assert "123.456.789" not in result
        assert "000.000.000-XX" in result

    def test_redacts_rg_in_plain_string(self):
        text = "RG: 1.234.567-8"
        result = _sanitize_pii_str(text)
        assert "1.234.567" not in result

    def test_no_pii_unchanged(self):
        text = "connection timeout after 30s"
        assert _sanitize_pii_str(text) == text


class TestLLMJudgeErrorPiiSanitized:
    def test_pii_in_exception_message_is_sanitized(self):
        spec = _make_spec()
        # ValueError is in the narrowed except tuple; tests that PII in the
        # exception message is sanitized before being stored in result.error.
        exc = ValueError("failed for CPF 123.456.789-09")
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, side_effect=exc)
        assert result.error is not None
        assert "123.456.789-09" not in result.error
        assert "000.000.000-XX" in result.error


class TestLLMJudgeMissingApiKey:
    def test_missing_key_returns_failed_result(self):
        spec = _make_spec()
        judge = LLMJudge()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge.grade({"field": "value"}, {"field": "value"}, spec)

        assert not result.passed
        assert result.score == 0.0
        assert "ANTHROPIC_API_KEY" in result.details

    def test_missing_key_preserves_weight(self):
        spec = _make_spec(weight=3.0)
        judge = LLMJudge()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge.grade({}, {}, spec)

        assert result.weight == 3.0

    def test_missing_key_preserves_field(self):
        spec = _make_spec(field="parecer")
        judge = LLMJudge()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge.grade({}, {}, spec)

        assert result.field == "parecer"


class TestLLMJudgeGrade:
    def test_perfect_score_passes(self):
        spec = _make_spec(config={"min_score": 4.0})
        response = _make_api_response(score=5, reasoning="Fully correct")
        result, _ = _mock_grade(LLMJudge(), {"text": "good"}, {"text": "good"}, spec, response)
        assert result.passed
        assert result.score == pytest.approx(1.0)

    def test_low_score_fails(self):
        spec = _make_spec(config={"min_score": 4.0})
        response = _make_api_response(score=2, reasoning="Major errors")
        result, _ = _mock_grade(LLMJudge(), {"text": "bad"}, {"text": "good"}, spec, response)
        assert not result.passed

    def test_score_normalization(self):
        spec = _make_spec(config={"min_score": 4.0})
        response = _make_api_response(score=3, reasoning="Partial")
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert result.score == pytest.approx(0.5)

    def test_min_score_boundary_passes(self):
        spec = _make_spec(config={"min_score": 4.0})
        response = _make_api_response(score=4, reasoning="Mostly correct")
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert result.passed

    def test_details_includes_score_and_reasoning(self):
        spec = _make_spec(config={"min_score": 4.0})
        response = _make_api_response(score=5, reasoning="All good")
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert "5" in result.details
        assert "All good" in result.details

    def test_grader_type_is_llm_judge(self):
        spec = _make_spec()
        response = _make_api_response(score=5)
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert result.grader_type == "llm_judge"

    def test_custom_rubric_in_config(self):
        spec = _make_spec(config={"rubric": "Check completeness", "min_score": 3.0})
        response = _make_api_response(score=4)
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert result.passed

    def test_custom_model_in_config(self):
        spec = _make_spec(config={"model": "claude-haiku-4-5", "min_score": 4.0})
        response = _make_api_response(score=5)
        _, mock_client = _mock_grade(LLMJudge(), {}, {}, spec, response)
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5"

    def test_pii_sanitized_before_api_call(self):
        spec = _make_spec()
        response = _make_api_response(score=5)
        output = {"cpf": "123.456.789-09"}
        expected = {"cpf": "123.456.789-09"}
        _, mock_client = _mock_grade(LLMJudge(), output, expected, spec, response)
        call_kwargs = mock_client.messages.create.call_args
        prompt_content = call_kwargs.kwargs["messages"][0]["content"]
        assert "123.456.789-09" not in prompt_content

    def test_field_propagated_to_result(self):
        spec = _make_spec(field="parecer")
        response = _make_api_response(score=5)
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert result.field == "parecer"

    def test_weight_propagated_to_result(self):
        spec = _make_spec(weight=2.5)
        response = _make_api_response(score=5)
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert result.weight == 2.5


class TestLLMJudgeEscapeHatch:
    def test_escape_hatch_returns_failed_result(self):
        spec = _make_spec()
        response = _make_api_response(score=3, reasoning="Cannot determine", escape_hatch=True)
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert not result.passed
        assert result.score == 0.0

    def test_escape_hatch_includes_reasoning_in_details(self):
        spec = _make_spec()
        response = _make_api_response(score=3, reasoning="Ambiguous document", escape_hatch=True)
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, response)
        assert "Ambiguous document" in result.details


class TestLLMJudgeApiError:
    def test_api_exception_returns_error_result(self):
        spec = _make_spec()
        # TimeoutError is in the narrowed except tuple and semantically correct
        # for a "connection timeout" scenario.
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, side_effect=TimeoutError("connection timeout"))
        assert not result.passed
        assert result.score == 0.0
        assert result.error is not None

    def test_api_error_includes_exception_type_in_error_field(self):
        spec = _make_spec()
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, side_effect=ValueError("invalid response"))
        assert result.error is not None
        assert "ValueError" in result.error

    def test_invalid_json_response_returns_error(self):
        from anthropic.types import TextBlock

        spec = _make_spec()
        bad_message = MagicMock()
        bad_message.content = [TextBlock(type="text", text="not valid json {{{")]
        result, _ = _mock_grade(LLMJudge(), {}, {}, spec, bad_message)
        assert not result.passed
        assert result.error is not None


def _make_rate_limit_error() -> anthropic.RateLimitError:
    import httpx

    req = httpx.Request("GET", "https://api.anthropic.com")
    resp = httpx.Response(429, request=req)
    return anthropic.RateLimitError("rate limited", response=resp, body=None)


def _make_bad_request_error() -> anthropic.BadRequestError:
    import httpx

    req = httpx.Request("GET", "https://api.anthropic.com")
    resp = httpx.Response(400, request=req)
    return anthropic.BadRequestError("bad request", response=resp, body=None)


class TestLLMJudgeRetry:
    def test_retry_on_rate_limit(self):
        """First call raises RateLimitError; second call succeeds. time.sleep is patched."""
        spec = _make_spec()
        success_response = _make_api_response(score=5, reasoning="OK")
        rate_limit_exc = _make_rate_limit_error()

        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch("gbr_eval.graders.model_judge.get_anthropic_client") as mock_get_client,
            patch("gbr_eval.graders.model_judge.time.sleep") as mock_sleep,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.messages.create.side_effect = [rate_limit_exc, success_response]
            result = LLMJudge().grade({}, {}, spec)

        assert result.passed
        assert result.score == pytest.approx(1.0)
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once_with(1.0)  # _BASE_DELAY * 2^0

    def test_retry_exhausted(self):
        """All calls raise RateLimitError; result carries the error."""
        spec = _make_spec()
        rate_limit_exc = _make_rate_limit_error()

        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch("gbr_eval.graders.model_judge.get_anthropic_client") as mock_get_client,
            patch("gbr_eval.graders.model_judge.time.sleep"),
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.messages.create.side_effect = rate_limit_exc
            result = LLMJudge().grade({}, {}, spec)

        assert not result.passed
        assert result.score == 0.0
        assert result.error is not None
        # Default _MAX_RETRIES=3 → 4 total attempts
        assert mock_client.messages.create.call_count == 4

    def test_no_retry_on_bad_request(self):
        """BadRequestError is not retried — only one attempt is made."""
        spec = _make_spec()
        bad_req_exc = _make_bad_request_error()

        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch("gbr_eval.graders.model_judge.get_anthropic_client") as mock_get_client,
            patch("gbr_eval.graders.model_judge.time.sleep") as mock_sleep,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.messages.create.side_effect = bad_req_exc
            result = LLMJudge().grade({}, {}, spec)

        assert not result.passed
        assert result.error is not None
        assert mock_client.messages.create.call_count == 1
        mock_sleep.assert_not_called()

    def test_max_retries_configurable(self):
        """spec.config['max_retries']=0 disables retry; only one attempt on rate limit."""
        spec = _make_spec(config={"max_retries": 0})
        rate_limit_exc = _make_rate_limit_error()

        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch("gbr_eval.graders.model_judge.get_anthropic_client") as mock_get_client,
            patch("gbr_eval.graders.model_judge.time.sleep") as mock_sleep,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.messages.create.side_effect = rate_limit_exc
            result = LLMJudge().grade({}, {}, spec)

        assert not result.passed
        assert result.error is not None
        assert mock_client.messages.create.call_count == 1
        mock_sleep.assert_not_called()
