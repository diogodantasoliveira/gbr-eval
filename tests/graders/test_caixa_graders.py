"""Tests for Caixa BPO graders: checklist_completeness, multi_step_calculation,
cross_document_match, array_sum_match, fuzzy_name_match, workflow_steps,
classification_accuracy, and semantic_interpretation.
"""

from __future__ import annotations

import os

import pytest

# Ensure all graders are registered
import gbr_eval.graders  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec, GraderStatus


def _spec(grader_type: str, field: str | None = None, **config: object) -> GraderSpec:
    return GraderSpec(type=grader_type, field=field, config=config)


# ---------------------------------------------------------------------------
# checklist_completeness
# ---------------------------------------------------------------------------


class TestChecklistCompleteness:
    def test_all_items_evaluated_pass(self):
        spec = _spec("checklist_completeness")
        output = {
            "checklist": [
                {"status": "aprovado"},
                {"status": "reprovado"},
                {"status": "verificado"},
            ]
        }
        result = grade("checklist_completeness", output, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_some_items_pending_fail(self):
        spec = _spec("checklist_completeness")
        output = {
            "checklist": [
                {"status": "aprovado"},
                {"status": "pendente"},
                {"status": "aprovado"},
                {"status": "nao_avaliado"},
            ]
        }
        result = grade("checklist_completeness", output, {}, spec)
        assert not result.passed
        assert result.score == pytest.approx(0.5)

    def test_empty_checklist_fail(self):
        spec = _spec("checklist_completeness")
        output = {"checklist": []}
        result = grade("checklist_completeness", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert result.details is not None and "empty" in result.details.lower()

    def test_custom_status_and_checklist_field(self):
        spec = _spec(
            "checklist_completeness",
            checklist_field="itens",
            status_field="situacao",
        )
        output = {
            "itens": [
                {"situacao": "ok"},
                {"situacao": "ok"},
            ]
        }
        result = grade("checklist_completeness", output, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_mix_of_evaluated_and_null_status(self):
        spec = _spec("checklist_completeness")
        output = {
            "checklist": [
                {"status": "aprovado"},
                {"status": None},
                {"status": "verificado"},
            ]
        }
        result = grade("checklist_completeness", output, {}, spec)
        # None is in the default unevaluated_values, so only 2 of 3 evaluated
        assert not result.passed
        assert result.score == pytest.approx(2 / 3)

    def test_missing_checklist_field_fail(self):
        spec = _spec("checklist_completeness")
        output = {}
        result = grade("checklist_completeness", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_checklist_not_array_fail(self):
        spec = _spec("checklist_completeness")
        output = {"checklist": "not-a-list"}
        result = grade("checklist_completeness", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# multi_step_calculation
# ---------------------------------------------------------------------------


class TestMultiStepCalculation:
    def test_all_steps_correct_pass(self):
        spec = _spec("multi_step_calculation")
        output = {
            "steps": [
                {"expected": 100.0, "actual": 100.0},
                {"expected": 50.0, "actual": 50.0},
                {"expected": 200.0, "actual": 200.0},
            ]
        }
        result = grade("multi_step_calculation", output, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_one_step_wrong_fail(self):
        spec = _spec("multi_step_calculation")
        output = {
            "steps": [
                {"expected": 100.0, "actual": 100.0},
                {"expected": 50.0, "actual": 999.0},
                {"expected": 200.0, "actual": 200.0},
            ]
        }
        result = grade("multi_step_calculation", output, {}, spec)
        assert not result.passed
        assert result.score == pytest.approx(2 / 3)

    def test_empty_steps_fail(self):
        spec = _spec("multi_step_calculation")
        output = {"steps": []}
        result = grade("multi_step_calculation", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_custom_tolerance_pass(self):
        # With 5% tolerance, 100 vs 104 should pass
        spec = _spec("multi_step_calculation", tolerance=0.05)
        output = {"steps": [{"expected": 100.0, "actual": 104.0}]}
        result = grade("multi_step_calculation", output, {}, spec)
        assert result.passed

    def test_custom_tolerance_fail(self):
        # With 1% tolerance, 100 vs 110 should fail
        spec = _spec("multi_step_calculation", tolerance=0.01)
        output = {"steps": [{"expected": 100.0, "actual": 110.0}]}
        result = grade("multi_step_calculation", output, {}, spec)
        assert not result.passed

    def test_steps_with_different_magnitudes(self):
        spec = _spec("multi_step_calculation", tolerance=0.01)
        output = {
            "steps": [
                {"expected": 1000000.0, "actual": 1009999.0},  # within 1%
                {"expected": 0.001, "actual": 0.001},
            ]
        }
        result = grade("multi_step_calculation", output, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_missing_steps_field_fail(self):
        spec = _spec("multi_step_calculation")
        output = {}
        result = grade("multi_step_calculation", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# cross_document_match
# ---------------------------------------------------------------------------


class TestCrossDocumentMatch:
    def test_matching_fields_pass(self):
        spec = _spec("cross_document_match", source_field="cpf", target_field="cpf")
        output = {"cpf": "123.456.789-09"}
        expected = {"cpf": "123.456.789-09"}
        result = grade("cross_document_match", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_non_matching_fields_fail(self):
        spec = _spec("cross_document_match", source_field="cpf", target_field="cpf")
        output = {"cpf": "000.000.000-00"}
        expected = {"cpf": "123.456.789-09"}
        result = grade("cross_document_match", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_case_insensitive_default(self):
        spec = _spec("cross_document_match", source_field="nome", target_field="nome")
        output = {"nome": "JOAO SILVA"}
        expected = {"nome": "joao silva"}
        result = grade("cross_document_match", output, expected, spec)
        assert result.passed

    def test_case_sensitive_config(self):
        spec = _spec(
            "cross_document_match",
            source_field="nome",
            target_field="nome",
            case_sensitive=True,
        )
        output = {"nome": "JOAO SILVA"}
        expected = {"nome": "joao silva"}
        result = grade("cross_document_match", output, expected, spec)
        assert not result.passed

    def test_missing_source_field_fail(self):
        spec = _spec("cross_document_match", source_field="cpf", target_field="cpf")
        output = {}
        expected = {"cpf": "123"}
        result = grade("cross_document_match", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_missing_target_field_fail(self):
        spec = _spec("cross_document_match", source_field="cpf", target_field="cpf")
        output = {"cpf": "123"}
        expected = {}
        result = grade("cross_document_match", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_fallback_to_spec_field(self):
        spec = _spec("cross_document_match", field="doc_number")
        output = {"doc_number": "ABC-123"}
        expected = {"doc_number": "ABC-123"}
        result = grade("cross_document_match", output, expected, spec)
        assert result.passed

    def test_no_fields_configured_fail(self):
        spec = _spec("cross_document_match")  # no source_field, no target_field, no field
        result = grade("cross_document_match", {}, {}, spec)
        assert not result.passed
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# array_sum_match
# ---------------------------------------------------------------------------


class TestArraySumMatch:
    def test_sum_matches_total_pass(self):
        spec = _spec("array_sum_match", field="parcelas", total_field="total")
        output = {"parcelas": [100.0, 200.0, 300.0]}
        expected = {"total": 600.0}
        result = grade("array_sum_match", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_sum_doesnt_match_total_fail(self):
        spec = _spec("array_sum_match", field="parcelas", total_field="total")
        output = {"parcelas": [100.0, 200.0]}
        expected = {"total": 600.0}
        result = grade("array_sum_match", output, expected, spec)
        assert not result.passed

    def test_array_of_objects_with_value_field(self):
        spec = _spec(
            "array_sum_match",
            field="itens",
            value_field="valor",
            total_field="total_esperado",
        )
        output = {"itens": [{"valor": 50.0}, {"valor": 75.0}, {"valor": 25.0}]}
        expected = {"total_esperado": 150.0}
        result = grade("array_sum_match", output, expected, spec)
        assert result.passed

    def test_empty_array_sum_zero(self):
        spec = _spec("array_sum_match", field="parcelas", total_field="total")
        output = {"parcelas": []}
        expected = {"total": 0.0}
        result = grade("array_sum_match", output, expected, spec)
        assert result.passed

    def test_within_tolerance(self):
        # Sum 100.005 vs expected 100.0 should pass with default 1% tolerance
        spec = _spec("array_sum_match", field="valores", total_field="total")
        output = {"valores": [50.003, 50.002]}
        expected = {"total": 100.0}
        result = grade("array_sum_match", output, expected, spec)
        assert result.passed

    def test_missing_field_fail(self):
        spec = _spec("array_sum_match", field="parcelas", total_field="total")
        output = {}
        expected = {"total": 100.0}
        result = grade("array_sum_match", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_no_total_field_config_fail(self):
        spec = _spec("array_sum_match", field="parcelas")
        output = {"parcelas": [100.0]}
        expected = {}
        result = grade("array_sum_match", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_no_field_config_fail(self):
        spec = _spec("array_sum_match", total_field="total")  # no field
        output = {"x": [1, 2]}
        expected = {"total": 3.0}
        result = grade("array_sum_match", output, expected, spec)
        assert not result.passed


# ---------------------------------------------------------------------------
# fuzzy_name_match
# ---------------------------------------------------------------------------


class TestFuzzyNameMatch:
    def test_exact_same_name_pass(self):
        spec = _spec("fuzzy_name_match", field="nome")
        output = {"nome": "Maria Santos"}
        expected = {"nome": "Maria Santos"}
        result = grade("fuzzy_name_match", output, expected, spec)
        assert result.passed
        assert result.score == pytest.approx(1.0)

    def test_accent_differences_pass(self):
        spec = _spec("fuzzy_name_match", field="nome")
        output = {"nome": "Joao Silva"}
        expected = {"nome": "João Silva"}
        result = grade("fuzzy_name_match", output, expected, spec)
        # normalize=True by default — accent stripped before comparison
        assert result.passed

    def test_very_different_names_fail(self):
        spec = _spec("fuzzy_name_match", field="nome")
        output = {"nome": "Carlos Pereira"}
        expected = {"nome": "Ana Lima"}
        result = grade("fuzzy_name_match", output, expected, spec)
        assert not result.passed

    def test_custom_threshold_low(self):
        spec = _spec("fuzzy_name_match", field="nome", threshold=0.5)
        output = {"nome": "Joo"}
        expected = {"nome": "Joao"}
        result = grade("fuzzy_name_match", output, expected, spec)
        # Low threshold — should pass
        assert result.passed

    def test_custom_threshold_high_strict_fail(self):
        spec = _spec("fuzzy_name_match", field="nome", threshold=0.999)
        output = {"nome": "Joao Silva"}
        expected = {"nome": "João Silva"}
        # After normalization they are identical (accent stripped) → should pass even with high threshold
        result = grade("fuzzy_name_match", output, expected, spec)
        assert result.passed  # normalized to "joao silva" == "joao silva"

    def test_names_with_extra_spaces_and_different_case(self):
        spec = _spec("fuzzy_name_match", field="nome", normalize=True)
        output = {"nome": "  JOAO   SILVA  "}
        expected = {"nome": "Joao Silva"}
        result = grade("fuzzy_name_match", output, expected, spec)
        assert result.passed

    def test_missing_field_fail(self):
        spec = _spec("fuzzy_name_match", field="nome")
        output = {}
        expected = {"nome": "Maria"}
        result = grade("fuzzy_name_match", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_no_field_spec_fail(self):
        spec = _spec("fuzzy_name_match")  # field=None
        result = grade("fuzzy_name_match", {"nome": "x"}, {"nome": "x"}, spec)
        assert not result.passed


# ---------------------------------------------------------------------------
# workflow_steps
# ---------------------------------------------------------------------------


class TestWorkflowSteps:
    def test_all_steps_correct_order_pass(self):
        spec = _spec("workflow_steps")
        output = {"etapas_executadas": ["validacao", "analise", "aprovacao"]}
        expected = {"etapas_esperadas": ["validacao", "analise", "aprovacao"]}
        result = grade("workflow_steps", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_missing_step_fail(self):
        spec = _spec("workflow_steps")
        output = {"etapas_executadas": ["validacao", "aprovacao"]}
        expected = {"etapas_esperadas": ["validacao", "analise", "aprovacao"]}
        result = grade("workflow_steps", output, expected, spec)
        assert not result.passed
        assert result.score < 1.0

    def test_steps_present_wrong_order_fail(self):
        spec = _spec("workflow_steps")
        output = {"etapas_executadas": ["aprovacao", "analise", "validacao"]}
        expected = {"etapas_esperadas": ["validacao", "analise", "aprovacao"]}
        result = grade("workflow_steps", output, expected, spec)
        assert not result.passed

    def test_extra_steps_in_output_still_pass(self):
        # Extra steps are irrelevant — only expected steps must be in order
        spec = _spec("workflow_steps")
        output = {
            "etapas_executadas": [
                "pre_check",
                "validacao",
                "extra_step",
                "analise",
                "aprovacao",
                "post_step",
            ]
        }
        expected = {"etapas_esperadas": ["validacao", "analise", "aprovacao"]}
        result = grade("workflow_steps", output, expected, spec)
        assert result.passed

    def test_empty_expected_steps_pass(self):
        spec = _spec("workflow_steps")
        output = {"etapas_executadas": ["validacao"]}
        expected = {"etapas_esperadas": []}
        result = grade("workflow_steps", output, expected, spec)
        assert result.passed
        assert result.score == 1.0

    def test_missing_output_field_fail(self):
        spec = _spec("workflow_steps")
        output = {}
        expected = {"etapas_esperadas": ["validacao"]}
        result = grade("workflow_steps", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_missing_expected_field_fail(self):
        spec = _spec("workflow_steps")
        output = {"etapas_executadas": ["validacao"]}
        expected = {}
        result = grade("workflow_steps", output, expected, spec)
        assert not result.passed
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# classification_accuracy
# ---------------------------------------------------------------------------


class TestClassificationAccuracy:
    def test_100_percent_accuracy_pass(self):
        spec = _spec("classification_accuracy")
        output = {
            "predictions": [
                {"predicted": "aprovado", "actual": "aprovado"},
                {"predicted": "reprovado", "actual": "reprovado"},
                {"predicted": "pendente", "actual": "pendente"},
            ]
        }
        result = grade("classification_accuracy", output, {}, spec)
        assert result.passed
        assert result.score == pytest.approx(1.0)

    def test_below_default_threshold_fail(self):
        spec = _spec("classification_accuracy")  # threshold=0.90
        output = {
            "predictions": [
                {"predicted": "aprovado", "actual": "aprovado"},
                {"predicted": "errado", "actual": "reprovado"},
                {"predicted": "errado", "actual": "pendente"},
            ]
        }
        result = grade("classification_accuracy", output, {}, spec)
        assert not result.passed
        assert result.score == pytest.approx(1 / 3)

    def test_custom_threshold_pass(self):
        spec = _spec("classification_accuracy", threshold=0.50)
        output = {
            "predictions": [
                {"predicted": "aprovado", "actual": "aprovado"},
                {"predicted": "errado", "actual": "reprovado"},
            ]
        }
        result = grade("classification_accuracy", output, {}, spec)
        assert result.passed
        assert result.score == pytest.approx(0.5)

    def test_case_insensitive_matching(self):
        spec = _spec("classification_accuracy", threshold=1.0)
        output = {
            "predictions": [
                {"predicted": "APROVADO", "actual": "aprovado"},
                {"predicted": "Reprovado", "actual": "reprovado"},
            ]
        }
        result = grade("classification_accuracy", output, {}, spec)
        assert result.passed
        assert result.score == pytest.approx(1.0)

    def test_empty_predictions_fail(self):
        spec = _spec("classification_accuracy")
        output = {"predictions": []}
        result = grade("classification_accuracy", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_missing_predictions_field_fail(self):
        spec = _spec("classification_accuracy")
        output = {}
        result = grade("classification_accuracy", output, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_custom_predictions_field(self):
        spec = _spec("classification_accuracy", predictions_field="resultados")
        output = {
            "resultados": [
                {"predicted": "ok", "actual": "ok"},
                {"predicted": "ok", "actual": "ok"},
            ]
        }
        result = grade("classification_accuracy", output, {}, spec)
        assert result.passed


# ---------------------------------------------------------------------------
# semantic_interpretation (skipped when no ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------


class TestSemanticInterpretation:
    def test_missing_api_key_returns_skipped(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        spec = _spec("semantic_interpretation", field="onus")
        output = {"onus": "alienacao fiduciaria em favor do Banco X"}
        expected = {"onus": "alienacao fiduciaria"}
        result = grade("semantic_interpretation", output, expected, spec)
        assert result.status == GraderStatus.SKIPPED
        assert not result.passed
        assert result.error is not None
        assert "ANTHROPIC_API_KEY" in result.error

    def test_missing_field_name_still_calls_grader(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        spec = _spec("semantic_interpretation")  # field=None
        output = {}
        expected = {}
        # With no API key, returns SKIPPED before field check
        result = grade("semantic_interpretation", output, expected, spec)
        assert result.status == GraderStatus.SKIPPED

    def test_with_api_key_present(self, monkeypatch: pytest.MonkeyPatch):
        """When ANTHROPIC_API_KEY is set, grader should attempt LLM call.
        We only verify it does NOT return SKIPPED status (may ERROR or GRADED
        depending on network availability in CI).
        """
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set — skipping live call test")

        spec = _spec(
            "semantic_interpretation",
            field="interpretacao",
            domain="juridico",
        )
        output = {"interpretacao": "sem onus na matricula"}
        expected = {"interpretacao": "matricula livre e desembaracada"}
        result = grade("semantic_interpretation", output, expected, spec)
        # Status should be GRADED or ERROR, never SKIPPED when key is present
        assert result.status != GraderStatus.SKIPPED
