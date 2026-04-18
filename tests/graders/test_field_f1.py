"""Tests for field F1 grader."""

from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec

import gbr_eval.graders.field_f1  # noqa: F401


class TestFieldF1:
    def test_perfect_match(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"cpf": "123.456.789-09", "nome": "João Silva", "area": 150.0}
        output = {"cpf": "123.456.789-09", "nome": "João Silva", "area": 150.0}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_all_missing(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"cpf": "123", "nome": "João"}
        output = {}
        result = grade("field_f1", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_partial_match(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.50})
        expected = {"cpf": "123", "nome": "João", "area": 100}
        output = {"cpf": "123", "nome": "Wrong", "area": 100}
        result = grade("field_f1", output, expected, spec)
        assert result.score > 0.0

    def test_fuzzy_match_names(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90, "fuzzy_ratio": 0.85})
        expected = {"nome": "João Carlos da Silva"}
        output = {"nome": "Joao Carlos da Silva"}
        result = grade("field_f1", output, expected, spec)
        assert result.passed

    def test_numeric_tolerance(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90, "numeric_tolerance": 0.01})
        expected = {"area": 150.0}
        output = {"area": 150.5}
        result = grade("field_f1", output, expected, spec)
        assert result.passed

    def test_critical_fields_only(self):
        spec = GraderSpec(
            type="field_f1",
            config={
                "scope": "critical_only",
                "critical_fields": ["cpf", "matricula"],
                "f1_threshold": 0.90,
            },
        )
        expected = {"cpf": "123", "matricula": "456", "endereco": "Rua X"}
        output = {"cpf": "123", "matricula": "456", "endereco": "WRONG"}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_extra_fields_in_output(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"cpf": "123"}
        output = {"cpf": "123", "extra": "field"}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
