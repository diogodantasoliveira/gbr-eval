"""Tests for deterministic graders."""


# Ensure graders are registered
import gbr_eval.graders  # noqa: F401
import gbr_eval.graders.deterministic  # noqa: F401
from gbr_eval.graders.base import _CONTEXT_AWARE, _REGISTRY, grade, register_grader
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

    def test_missing_field(self):
        spec = GraderSpec(
            type="set_membership",
            field="decision",
            config={"valid_values": ["aprovado", "reprovado"]},
        )
        result = grade("set_membership", {}, {}, spec)
        assert not result.passed
        assert "not found" in result.details


class TestStringContains:
    def test_substring_found(self):
        spec = GraderSpec(type="string_contains", field="parecer", config={"substring": "conforme"})
        result = grade("string_contains", {"parecer": "Documento conforme com as normas"}, {}, spec)
        assert result.passed

    def test_substring_not_found(self):
        spec = GraderSpec(type="string_contains", field="parecer", config={"substring": "irregular"})
        result = grade("string_contains", {"parecer": "Tudo certo"}, {}, spec)
        assert not result.passed


class TestExactMatchNoneHandling:
    def test_none_actual_fails_even_when_expected_is_none(self):
        """actual=None must always fail — None means field not found in output."""
        spec = GraderSpec(type="exact_match", field="cpf")
        result = grade("exact_match", {}, {}, spec)  # expected also has no cpf → reference=None
        assert not result.passed
        assert result.score == 0.0

    def test_none_actual_fails_when_expected_is_value(self):
        spec = GraderSpec(type="exact_match", field="cpf")
        result = grade("exact_match", {}, {"cpf": "123"}, spec)
        assert not result.passed

    def test_null_value_matches_null_expected(self):
        """Field present with None value should pass when expected is also None."""
        spec = GraderSpec(type="exact_match", field="validade")
        result = grade("exact_match", {"validade": None}, {"validade": None}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_null_value_fails_when_expected_is_value(self):
        spec = GraderSpec(type="exact_match", field="validade")
        result = grade("exact_match", {"validade": None}, {"validade": "25/01/2026"}, spec)
        assert not result.passed


class TestRegexMatchEdgeCases:
    def test_invalid_regex_returns_error_result(self):
        spec = GraderSpec(type="regex_match", field="cpf", config={"pattern": r"[invalid(regex"})
        result = grade("regex_match", {"cpf": "anything"}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "Invalid regex" in result.details

    def test_long_input_is_truncated(self):
        """Input longer than _REGEX_MAX_INPUT_LEN should still match at the start (no crash)."""
        long_value = "abc" * 5000  # 15 000 chars, well above 10 000 limit
        spec = GraderSpec(type="regex_match", field="text", config={"pattern": r"^abc"})
        result = grade("regex_match", {"text": long_value}, {}, spec)
        # Pattern matches at start — truncation keeps the beginning intact
        assert result.passed

    def test_long_input_truncation_prevents_match_beyond_limit(self):
        """Content only past the 10 000-char mark should NOT be matched."""
        prefix = "x" * 10_000
        tail = "TARGET"
        long_value = prefix + tail
        spec = GraderSpec(type="regex_match", field="text", config={"pattern": r"TARGET"})
        result = grade("regex_match", {"text": long_value}, {}, spec)
        assert not result.passed


class TestNumericToleranceMissingDetails:
    def test_missing_actual_shows_readable_message(self):
        spec = GraderSpec(type="numeric_tolerance", field="value", config={"tolerance": 0.01})
        result = grade("numeric_tolerance", {}, {"value": 100}, spec)
        assert not result.passed
        assert "field missing" in result.details
        assert "object at" not in result.details

    def test_missing_expected_shows_readable_message(self):
        spec = GraderSpec(type="numeric_tolerance", field="value", config={"tolerance": 0.01})
        result = grade("numeric_tolerance", {"value": 100}, {}, spec)
        assert not result.passed
        assert "field missing" in result.details


class TestStringContainsFalsyExpected:
    def test_falsy_expected_value_zero_still_matches(self):
        spec = GraderSpec(type="string_contains", field="code")
        result = grade("string_contains", {"code": "code is 0"}, {"code": 0}, spec)
        assert result.passed

    def test_falsy_expected_value_false_still_matches(self):
        spec = GraderSpec(type="string_contains", field="flag")
        result = grade("string_contains", {"flag": "value is False"}, {"flag": False}, spec)
        assert result.passed


class TestRegexPatternLengthCap:
    def test_oversized_pattern_rejected(self):
        long_pattern = "a" * 1_001
        spec = GraderSpec(type="regex_match", field="text", config={"pattern": long_pattern})
        result = grade("regex_match", {"text": "anything"}, {}, spec)
        assert not result.passed
        assert "Pattern too long" in result.details

    def test_max_length_pattern_accepted(self):
        pattern = "a" * 1_000
        spec = GraderSpec(type="regex_match", field="text", config={"pattern": pattern})
        result = grade("regex_match", {"text": "a" * 1_000}, {}, spec)
        assert result.passed


class TestBaseGradeErrorMessage:
    def test_error_includes_exception_type_name(self):
        """grade() wraps ValueError/TypeError/AttributeError with the type name."""
        # Provoke a TypeError by registering a spec whose grader will raise internally.
        # Easiest path: pass a non-dict output to a grader that calls .get() on it.
        # We instead test via an unknown grader (KeyError path) and verify format.
        spec = GraderSpec(type="__no_such_grader__", field="x")
        result = grade("__no_such_grader__", {}, {}, spec)
        assert not result.passed
        assert result.error is not None
        # KeyError path wraps with "KeyError:"
        assert "KeyError" in result.error


class TestContextAwareRegistry:
    def test_llm_judge_in_context_aware_set(self):
        """llm_judge must be registered as context-aware."""
        assert "llm_judge" in _CONTEXT_AWARE

    def test_deterministic_graders_not_in_context_aware(self):
        """Deterministic graders must NOT appear in _CONTEXT_AWARE."""
        deterministic_names = [
            "exact_match",
            "numeric_range",
            "numeric_tolerance",
            "regex_match",
            "field_not_empty",
            "set_membership",
            "string_contains",
        ]
        for name in deterministic_names:
            assert name not in _CONTEXT_AWARE, f"{name!r} should not be context-aware"

    def test_register_grader_context_aware_flag(self):
        """Registering with context_aware=True adds the name to _CONTEXT_AWARE."""
        test_name = "__test_context_aware_grader__"
        # Ensure the name is not already present
        assert test_name not in _REGISTRY
        assert test_name not in _CONTEXT_AWARE

        @register_grader(test_name, context_aware=True)
        class _TestContextAwareGrader:
            def grade(self, output, expected, spec):  # noqa: ANN001
                from gbr_eval.harness.models import GraderResult
                return GraderResult(
                    grader_type=test_name,
                    field=spec.field,
                    passed=True,
                    score=1.0,
                    weight=spec.weight,
                    required=spec.required,
                )

        try:
            assert test_name in _CONTEXT_AWARE
            assert test_name in _REGISTRY
        finally:
            # Clean up to avoid polluting other tests
            _REGISTRY.pop(test_name, None)
            _CONTEXT_AWARE.discard(test_name)
