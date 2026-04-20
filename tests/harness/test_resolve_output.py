"""Tests for _resolve_output in gbr_eval.harness.runner."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from gbr_eval.harness.client import EvalClient, EvalClientError, OutputRecorder
from gbr_eval.harness.models import Category, GraderSpec, Layer, Task, TaskInput
from gbr_eval.harness.runner import _resolve_output, run_task_against_golden_set


def _make_task(endpoint: str = "/api/extract") -> Task:
    return Task(
        task_id="test.task",
        category=Category.EXTRACTION,
        component="test",
        layer=Layer.PRODUCT,
        input=TaskInput(endpoint=endpoint, payload={"skill": "matricula_v1"}),
        graders=[GraderSpec(type="exact_match", config={"field": "x"})],
    )


class TestResolveOutput:
    def test_resolve_self_eval_returns_expected(self) -> None:
        task = _make_task()
        case = {
            "case_number": 1,
            "expected_output": {"cpf": "123.456.789-09", "nome": "João"},
        }

        result = _resolve_output(case, task, self_eval=True)

        assert result == {"cpf": "123.456.789-09", "nome": "João"}

    def test_resolve_self_eval_includes_citation(self) -> None:
        task = _make_task()
        case = {
            "case_number": 1,
            "expected_output": {"cpf": "123.456.789-09"},
            "citation": {"page": 1, "text": "CPF do titular"},
        }

        result = _resolve_output(case, task, self_eval=True)

        assert result["citation"] == {"page": 1, "text": "CPF do titular"}
        assert result["cpf"] == "123.456.789-09"

    def test_resolve_replay_from_recorder(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        saved_output = {"cpf": "987.654.321-00", "score": 0.95}
        recorder.save("test.task", 2, saved_output)

        task = _make_task()
        case = {"case_number": 2, "expected_output": {"cpf": "987.654.321-00"}}

        result = _resolve_output(case, task, self_eval=False, recorder=recorder)

        assert result == saved_output

    def test_resolve_empty_when_no_mode(self) -> None:
        task = _make_task()
        case = {"case_number": 1, "expected_output": {"cpf": "123"}}

        result = _resolve_output(case, task, self_eval=False, client=None, recorder=None)

        assert result == {}

    def test_resolve_self_eval_does_not_mutate_case(self) -> None:
        task = _make_task()
        expected = {"cpf": "000.000.000-11"}
        case = {"case_number": 1, "expected_output": expected}

        result = _resolve_output(case, task, self_eval=True)
        result["injected"] = "mutation"

        assert "injected" not in case["expected_output"]

    def test_resolve_replay_missing_case_falls_through_to_empty(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        task = _make_task()
        case = {"case_number": 99, "expected_output": {"cpf": "123"}}

        result = _resolve_output(case, task, self_eval=False, recorder=recorder)

        assert result == {}

    def test_resolve_self_eval_without_citation_field(self) -> None:
        task = _make_task()
        case = {
            "case_number": 1,
            "expected_output": {"field": "value"},
        }

        result = _resolve_output(case, task, self_eval=True)

        assert "citation" not in result
        assert result == {"field": "value"}

    def test_self_eval_takes_precedence_over_recorder(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        # Save different data into the recorder for the same case
        recorder.save("test.task", 1, {"cpf": "recorder-value"})

        task = _make_task()
        case = {
            "case_number": 1,
            "expected_output": {"cpf": "self-eval-value"},
        }

        result = _resolve_output(case, task, self_eval=True, recorder=recorder)

        assert result == {"cpf": "self-eval-value"}

    def test_resolve_with_client_and_recorder_records(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        api_response = {"cpf": "from-api", "score": 0.99}

        task = _make_task(endpoint="/api/extract")
        case = {"case_number": 3, "expected_output": {"cpf": "from-api"}}

        with patch.object(EvalClient, "call", return_value=api_response) as mock_call:
            client = EvalClient(base_url="http://localhost:8000", allow_internal=True)
            result = _resolve_output(case, task, self_eval=False, client=client, recorder=recorder)

        assert result == api_response
        mock_call.assert_called_once()
        saved = recorder.load("test.task", 3)
        assert saved == api_response

    def test_resolve_warns_when_no_source(self) -> None:
        task = _make_task()
        case = {"case_number": 1, "expected_output": {"cpf": "123"}}

        with pytest.warns(UserWarning, match="No output source"):
            result = _resolve_output(case, task, self_eval=False, client=None, recorder=None)

        assert result == {}


def test_eval_client_error_does_not_crash_golden_set() -> None:
    """EvalClientError from a single case must not crash the entire golden set run."""
    from unittest.mock import patch

    task = _make_task(endpoint="/api/extract")
    cases = [
        {"case_number": 1, "expected_output": {"cpf": "000.000.000-11"}},
    ]

    with patch.object(EvalClient, "call", side_effect=EvalClientError("connection refused")):
        client = EvalClient(base_url="http://localhost:8000", allow_internal=True)
        result = run_task_against_golden_set(task, cases, self_eval=False, client=client)

    assert result.passed is False
    assert result.score == 0.0
