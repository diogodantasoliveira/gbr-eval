"""Tests for HaikuTriage grader — fast binary triage for the grading funnel."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gbr_eval.graders.haiku_triage import HaikuTriage
from gbr_eval.harness.models import GraderSpec


def _make_spec(**overrides: object) -> GraderSpec:
    defaults = {
        "type": "haiku_triage",
        "field": "triage",
        "config": {"rubric": "Check for security issues", "file_key": "content"},
    }
    defaults.update(overrides)
    return GraderSpec(**defaults)  # type: ignore[arg-type]


class TestHaikuTriage:
    def test_no_api_key_fails_open(self) -> None:
        grader = HaikuTriage()
        spec = _make_spec()
        with patch.dict("os.environ", {}, clear=True):
            result = grader.grade({"content": "code"}, {}, spec)
        assert result.passed is False
        assert "[fail-open]" in result.details

    def test_empty_file_skips(self) -> None:
        grader = HaikuTriage()
        spec = _make_spec()
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}):
            result = grader.grade({"content": "   "}, {}, spec)
        assert result.passed is True
        assert "Empty file" in result.details

    def test_no_rubric_fails_open(self) -> None:
        grader = HaikuTriage()
        spec = _make_spec(config={"file_key": "content"})
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}):
            result = grader.grade({"content": "code"}, {}, spec)
        assert result.passed is False
        assert "[fail-open]" in result.details

    def test_needs_review_true(self) -> None:
        grader = HaikuTriage()
        spec = _make_spec()

        mock_text = MagicMock()
        mock_text.text = '{"needs_deep_review": true, "reason": "has eval()", "confidence": 0.9}'

        mock_response = MagicMock()
        mock_response.content = [mock_text]
        type(mock_text).__name__ = "TextBlock"

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
             patch("gbr_eval.graders.haiku_triage.anthropic.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            with patch("gbr_eval.graders.haiku_triage.isinstance", side_effect=lambda obj, cls: True):
                result = grader.grade({"content": "eval('danger')"}, {}, spec)

        assert result.passed is False
        assert result.score == 0.0
        assert "needs_review=True" in result.details

    def test_needs_review_false(self) -> None:
        grader = HaikuTriage()
        spec = _make_spec()

        mock_text = MagicMock()
        mock_text.text = '{"needs_deep_review": false, "reason": "config only", "confidence": 0.95}'

        mock_response = MagicMock()
        mock_response.content = [mock_text]

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
             patch("gbr_eval.graders.haiku_triage.anthropic.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            with patch("gbr_eval.graders.haiku_triage.isinstance", side_effect=lambda obj, cls: True):
                result = grader.grade({"content": "export default {}"}, {}, spec)

        assert result.passed is True
        assert result.score == 1.0
        assert "needs_review=False" in result.details

    def test_api_error_fails_open(self) -> None:
        grader = HaikuTriage()
        spec = _make_spec()

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
             patch("gbr_eval.graders.haiku_triage.anthropic.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.side_effect = TimeoutError("timeout")
            result = grader.grade({"content": "code"}, {}, spec)

        assert result.passed is False
        assert "[fail-open]" in result.details
