"""Tests for contract validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gbr_eval.contracts.validator import ContractResult, validate_response
from gbr_eval.harness.models import EvalRun, GraderResult, Task, TaskResult

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "contracts" / "schemas"


@pytest.fixture()
def schema_path(tmp_path: Path) -> Path:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "ExtractResponse",
        "description": "Schema snapshot — AI engine extraction response",
        "type": "object",
        "required": ["document_type", "fields", "confidence"],
        "properties": {
            "document_type": {"type": "string"},
            "fields": {"type": "object"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    }
    p = tmp_path / "sample_extract_response.json"
    p.write_text(json.dumps(schema), encoding="utf-8")
    return p


class TestValidateResponseRequired:
    def test_pass_when_all_required_fields_present(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {"cpf": "000.000.000-00"}, "confidence": 0.95}
        result = validate_response(response, schema_path)
        assert result.valid
        assert result.errors == []

    def test_fail_when_required_field_missing(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {}}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("confidence" in e for e in result.errors)

    def test_fail_when_multiple_required_fields_missing(self, schema_path: Path) -> None:
        result = validate_response({}, schema_path)
        assert not result.valid
        assert len(result.errors) == 3

    def test_fail_when_single_required_field_missing(self, schema_path: Path) -> None:
        response = {"fields": {}, "confidence": 0.5}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("document_type" in e for e in result.errors)


class TestValidateResponseTypes:
    def test_fail_when_string_field_is_not_string(self, schema_path: Path) -> None:
        response = {"document_type": 42, "fields": {}, "confidence": 0.9}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("document_type" in e for e in result.errors)

    def test_fail_when_object_field_is_not_dict(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": "not_a_dict", "confidence": 0.9}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("fields" in e for e in result.errors)

    def test_fail_when_number_field_is_string(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {}, "confidence": "high"}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("confidence" in e for e in result.errors)

    def test_pass_when_integer_used_for_number_field(self, schema_path: Path) -> None:
        # JSON Schema "number" accepts integers
        response = {"document_type": "matricula", "fields": {}, "confidence": 1}
        result = validate_response(response, schema_path)
        assert result.valid

    def test_fail_when_bool_used_for_number_field(self, schema_path: Path) -> None:
        # booleans are not valid numbers in JSON Schema
        response = {"document_type": "matricula", "fields": {}, "confidence": True}
        result = validate_response(response, schema_path)
        assert not result.valid


class TestValidateResponseNumericConstraints:
    def test_fail_when_confidence_below_minimum(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {}, "confidence": -0.1}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("minimum" in e for e in result.errors)

    def test_fail_when_confidence_above_maximum(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {}, "confidence": 1.5}
        result = validate_response(response, schema_path)
        assert not result.valid
        assert any("maximum" in e for e in result.errors)

    def test_pass_at_boundary_values(self, schema_path: Path) -> None:
        for boundary in (0, 1, 0.0, 1.0):
            response = {"document_type": "matricula", "fields": {}, "confidence": boundary}
            result = validate_response(response, schema_path)
            assert result.valid, f"Expected valid at boundary {boundary}, errors: {result.errors}"


class TestContractResult:
    def test_schema_version_set_from_title(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {}, "confidence": 0.9}
        result = validate_response(response, schema_path)
        assert result.schema_version == "ExtractResponse"

    def test_returns_contract_result_instance(self, schema_path: Path) -> None:
        response = {"document_type": "matricula", "fields": {}, "confidence": 0.9}
        result = validate_response(response, schema_path)
        assert isinstance(result, ContractResult)

    def test_extra_fields_are_allowed(self, schema_path: Path) -> None:
        response = {
            "document_type": "matricula",
            "fields": {},
            "confidence": 0.9,
            "extra_field": "ignored",
        }
        result = validate_response(response, schema_path)
        assert result.valid


class TestSampleSchemaOnDisk:
    def test_validate_against_real_schema_file(self) -> None:
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "schemas" / "sample_extract_response.json"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"
        response = {"document_type": "matricula", "fields": {"cpf": "000.000.000-00"}, "confidence": 0.97}
        result = validate_response(response, schema_path)
        assert result.valid

    def test_real_schema_rejects_invalid_response(self) -> None:
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "schemas" / "sample_extract_response.json"
        result = validate_response({"document_type": "matricula"}, schema_path)
        assert not result.valid


class TestHarnessModelSchemas:
    """Catch drift between on-disk JSON Schemas and live Pydantic model definitions.

    If a model field is added, removed, or renamed, the on-disk snapshot will
    diverge and these tests will fail — signalling that `tools/export_schemas.py`
    must be re-run before merging.
    """

    def test_eval_run_schema_matches_model(self) -> None:
        schema_path = SCHEMAS_DIR / "eval_run.json"
        assert schema_path.exists(), f"Schema file not found: {schema_path}. Run tools/export_schemas.py."
        on_disk = json.loads(schema_path.read_text(encoding="utf-8"))
        assert on_disk == EvalRun.model_json_schema(), (
            "eval_run.json is out of sync with EvalRun. Re-run tools/export_schemas.py."
        )

    def test_task_schema_matches_model(self) -> None:
        schema_path = SCHEMAS_DIR / "task.json"
        assert schema_path.exists(), f"Schema file not found: {schema_path}. Run tools/export_schemas.py."
        on_disk = json.loads(schema_path.read_text(encoding="utf-8"))
        assert on_disk == Task.model_json_schema(), (
            "task.json is out of sync with Task. Re-run tools/export_schemas.py."
        )

    def test_task_result_schema_matches_model(self) -> None:
        schema_path = SCHEMAS_DIR / "task_result.json"
        assert schema_path.exists(), f"Schema file not found: {schema_path}. Run tools/export_schemas.py."
        on_disk = json.loads(schema_path.read_text(encoding="utf-8"))
        assert on_disk == TaskResult.model_json_schema(), (
            "task_result.json is out of sync with TaskResult. Re-run tools/export_schemas.py."
        )

    def test_grader_result_schema_matches_model(self) -> None:
        schema_path = SCHEMAS_DIR / "grader_result.json"
        assert schema_path.exists(), f"Schema file not found: {schema_path}. Run tools/export_schemas.py."
        on_disk = json.loads(schema_path.read_text(encoding="utf-8"))
        assert on_disk == GraderResult.model_json_schema(), (
            "grader_result.json is out of sync with GraderResult. Re-run tools/export_schemas.py."
        )
