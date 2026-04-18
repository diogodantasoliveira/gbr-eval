"""Tests for deterministic graders."""


# Ensure graders are registered
import gbr_eval.graders.deterministic  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec


class TestExactMatch:
    def test_pass_when_equal(self):
        spec = GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True)
        result = grade("exact_match", {"cpf": "123.456.789-09"}, {"cpf": "123.456.789-09"}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_fail_when_different(self):
        spec = GraderSpec(type="exact_match", field="cpf", weight=3.0)
        result = grade("exact_match", {"cpf": "000.000.000-00"}, {"cpf": "123.456.789-09"}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_case_insensitive(self):
        spec = GraderSpec(type="exact_match", field="nome", config={"case_sensitive": False})
        result = grade("exact_match", {"nome": "JOÃO SILVA"}, {"nome": "João Silva"}, spec)
        assert result.passed

    def test_nested_field(self):
        spec = GraderSpec(type="exact_match", field="citation.cpf")
        output = {"citation": {"cpf": "123"}}
        expected = {"citation": {"cpf": "123"}}
        result = grade("exact_match", output, expected, spec)
        assert result.passed

    def test_missing_field(self):
        spec = GraderSpec(type="exact_match", field="missing")
        result = grade("exact_match", {}, {"missing": "value"}, spec)
        assert not result.passed


class TestNumericRange:
    def test_within_range(self):
        spec = GraderSpec(type="numeric_range", field="cost", config={"min": 0, "max": 50})
        result = grade("numeric_range", {"cost": 35.0}, {}, spec)
        assert result.passed

    def test_above_max(self):
        spec = GraderSpec(type="numeric_range", field="cost", config={"min": 0, "max": 50})
        result = grade("numeric_range", {"cost": 80.0}, {}, spec)
        assert not result.passed

    def test_below_min(self):
        spec = GraderSpec(type="numeric_range", field="score", config={"min": 0.90})
        result = grade("numeric_range", {"score": 0.5}, {}, spec)
        assert not result.passed

    def test_at_boundary(self):
        spec = GraderSpec(type="numeric_range", field="score", config={"min": 0.90, "max": 1.0})
        result = grade("numeric_range", {"score": 0.90}, {}, spec)
        assert result.passed


class TestNumericTolerance:
    def test_within_tolerance(self):
        spec = GraderSpec(type="numeric_tolerance", field="area", config={"tolerance": 0.01})
        result = grade("numeric_tolerance", {"area": 100.5}, {"area": 100.0}, spec)
        assert result.passed

    def test_outside_tolerance(self):
        spec = GraderSpec(type="numeric_tolerance", field="area", config={"tolerance": 0.01})
        result = grade("numeric_tolerance", {"area": 200.0}, {"area": 100.0}, spec)
        assert not result.passed


class TestRegexMatch:
    def test_cpf_pattern(self):
        spec = GraderSpec(type="regex_match", field="cpf", config={"pattern": r"\d{3}\.\d{3}\.\d{3}-\d{2}"})
        result = grade("regex_match", {"cpf": "123.456.789-09"}, {}, spec)
        assert result.passed

    def test_no_match(self):
        spec = GraderSpec(type="regex_match", field="cpf", config={"pattern": r"\d{3}\.\d{3}\.\d{3}-\d{2}"})
        result = grade("regex_match", {"cpf": "invalid"}, {}, spec)
        assert not result.passed


class TestFieldNotEmpty:
    def test_present(self):
        spec = GraderSpec(type="field_not_empty", field="citation.cpf")
        result = grade("field_not_empty", {"citation": {"cpf": "123"}}, {}, spec)
        assert result.passed

    def test_none(self):
        spec = GraderSpec(type="field_not_empty", field="citation.cpf")
        result = grade("field_not_empty", {"citation": {"cpf": None}}, {}, spec)
        assert not result.passed

    def test_empty_string(self):
        spec = GraderSpec(type="field_not_empty", field="name")
        result = grade("field_not_empty", {"name": ""}, {}, spec)
        assert not result.passed

    def test_missing_path(self):
        spec = GraderSpec(type="field_not_empty", field="deep.nested.field")
        result = grade("field_not_empty", {"other": "value"}, {}, spec)
        assert not result.passed


class TestSetMembership:
    def test_valid_value(self):
        spec = GraderSpec(
            type="set_membership",
            field="decision",
            config={"valid_values": ["aprovado", "reprovado", "inconclusivo", "aprovado_com_ressalvas"]},
        )
        result = grade("set_membership", {"decision": "aprovado"}, {}, spec)
        assert result.passed

    def test_invalid_value(self):
        spec = GraderSpec(
            type="set_membership",
            field="decision",
            config={"valid_values": ["aprovado", "reprovado"]},
        )
        result = grade("set_membership", {"decision": "maybe"}, {}, spec)
        assert not result.passed


class TestStringContains:
    def test_substring_found(self):
        spec = GraderSpec(type="string_contains", field="parecer", config={"substring": "conforme"})
        result = grade("string_contains", {"parecer": "Documento conforme com as normas"}, {}, spec)
        assert result.passed

    def test_substring_not_found(self):
        spec = GraderSpec(type="string_contains", field="parecer", config={"substring": "irregular"})
        result = grade("string_contains", {"parecer": "Tudo certo"}, {}, spec)
        assert not result.passed
