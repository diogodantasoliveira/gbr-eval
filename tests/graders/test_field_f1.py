"""Tests for field F1 grader."""

import gbr_eval.graders.field_f1  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec


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


class TestFieldF1ListComparison:
    def test_list_field_matching_passes(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"socios": ["João Silva", "Maria Santos"]}
        output = {"socios": ["João Silva", "Maria Santos"]}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_list_field_different_order_passes(self):
        """List comparison uses set-like matching — order independent."""
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"socios": ["Maria Santos", "João Silva"]}
        output = {"socios": ["João Silva", "Maria Santos"]}
        result = grade("field_f1", output, expected, spec)
        assert result.passed

    def test_list_field_wrong_values_fails(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"socios": ["João Silva", "Maria Santos"]}
        output = {"socios": ["Pedro Alves", "Carlos Lima"]}
        result = grade("field_f1", output, expected, spec)
        assert not result.passed
        assert result.score < 1.0

    def test_list_field_wrong_length_fails(self):
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"socios": ["João Silva", "Maria Santos"]}
        output = {"socios": ["João Silva"]}
        result = grade("field_f1", output, expected, spec)
        assert not result.passed

    def test_list_vs_non_list_fails(self):
        """If expected is a list but actual is a scalar, comparison must fail."""
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"socios": ["João Silva"]}
        output = {"socios": "João Silva"}
        result = grade("field_f1", output, expected, spec)
        assert not result.passed


class TestFieldF1MissingSentinel:
    def test_missing_field_counts_as_false_negative(self):
        """Absent field (not in dict) must be a FN, distinct from null."""
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"cpf": "123", "nome": "João"}
        output = {"cpf": "123"}
        result = grade("field_f1", output, expected, spec)
        assert "FN=1" in result.details

    def test_null_vs_null_counts_as_true_positive(self):
        """Both null = legitimate match, not a miss."""
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.90})
        expected = {"cpf": "123", "validade": None}
        output = {"cpf": "123", "validade": None}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_null_output_vs_valued_expected_is_fn(self):
        """Output has field as null but expected has a value = FN."""
        spec = GraderSpec(type="field_f1", config={"f1_threshold": 0.50})
        expected = {"cpf": "123", "validade": "25/01/2026"}
        output = {"cpf": "123", "validade": None}
        result = grade("field_f1", output, expected, spec)
        assert "FN=1" in result.details


class TestFieldF1SpecFieldScope:
    """C1 fix: when spec.field is set, only evaluate that single field."""

    def test_spec_field_evaluates_single_field(self):
        spec = GraderSpec(type="field_f1", field="cpf", config={"f1_threshold": 0.90})
        expected = {"cpf": "123", "nome": "Wrong", "area": 0}
        output = {"cpf": "123", "nome": "Different", "area": 999}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
        assert result.score == 1.0
        assert "TP=1" in result.details

    def test_spec_field_overrides_scope_all(self):
        spec = GraderSpec(type="field_f1", field="nome", config={"scope": "all", "f1_threshold": 0.90})
        expected = {"cpf": "wrong", "nome": "João"}
        output = {"cpf": "different", "nome": "João"}
        result = grade("field_f1", output, expected, spec)
        assert result.passed

    def test_spec_field_missing_in_output_fails(self):
        spec = GraderSpec(type="field_f1", field="cpf", config={"f1_threshold": 0.90})
        expected = {"cpf": "123", "nome": "João"}
        output = {"nome": "João"}
        result = grade("field_f1", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0


class TestFieldF1BoolIntConfusion:
    """M fix: bool/int comparison must check type, not just value."""

    def test_int_1_does_not_match_bool_true(self):
        from gbr_eval.graders.field_f1 import _compare_field
        assert not _compare_field(1, True, 0.85, 0.01)

    def test_int_0_does_not_match_bool_false(self):
        from gbr_eval.graders.field_f1 import _compare_field
        assert not _compare_field(0, False, 0.85, 0.01)

    def test_bool_true_matches_bool_true(self):
        from gbr_eval.graders.field_f1 import _compare_field
        assert _compare_field(True, True, 0.85, 0.01)

    def test_bool_false_matches_bool_false(self):
        from gbr_eval.graders.field_f1 import _compare_field
        assert _compare_field(False, False, 0.85, 0.01)


class TestFieldF1CriticalOnlyEmpty:
    """M fix: scope=critical_only with empty critical_fields returns error."""

    def test_critical_only_empty_fields_returns_error(self):
        spec = GraderSpec(type="field_f1", config={"scope": "critical_only", "critical_fields": []})
        expected = {"cpf": "123"}
        output = {"cpf": "123"}
        result = grade("field_f1", output, expected, spec)
        assert not result.passed
        assert "no critical_fields configured" in result.details

    def test_critical_only_with_spec_field_overrides(self):
        spec = GraderSpec(type="field_f1", field="cpf", config={"scope": "critical_only"})
        expected = {"cpf": "123", "nome": "João"}
        output = {"cpf": "123", "nome": "Wrong"}
        result = grade("field_f1", output, expected, spec)
        assert result.passed
