"""Integration smoke tests — golden sets fed through graders produce expected scores."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gbr_eval.harness.runner import load_task, run_task

GOLDEN_DIR = Path("golden")
TASKS_DIR = Path("tasks/product")

EXTRACTION_TASKS = [
    ("certidao_trabalhista", "extraction/certidao_trabalhista_extraction.yaml"),
    ("cnd", "extraction/cnd_extraction.yaml"),
    ("contrato_social", "extraction/contrato_social_extraction.yaml"),
    ("procuracao", "extraction/procuracao_extraction.yaml"),
    ("matricula", "extraction/matricula_cpf.yaml"),
]


def _load_cases(skill: str, *, tags: list[str] | None = None) -> list[dict]:
    skill_dir = GOLDEN_DIR / skill
    cases = []
    for f in sorted(skill_dir.glob("case_[0-9]*.json")):
        cases.append(json.loads(f.read_text()))
    if tags:
        cases = [c for c in cases if any(t in c.get("tags", []) for t in tags)]
    return cases


@pytest.mark.parametrize("skill,task_file", EXTRACTION_TASKS, ids=[s for s, _ in EXTRACTION_TASKS])
class TestPerfectExtraction:
    def test_perfect_extraction_scores_one(self, skill: str, task_file: str) -> None:
        task = load_task(TASKS_DIR / task_file)
        for case in _load_cases(skill, tags=["seed"]):
            expected = case["expected_output"]
            task.expected = expected
            result = run_task(task, expected)
            failed = [g.field for g in result.grader_results if not g.passed]
            assert result.passed, f"case_{case['case_number']:03d} failed: {failed}"
            assert result.score == 1.0


class TestGradersCatchErrors:
    def test_wrong_resultado_fails(self) -> None:
        case = json.loads((GOLDEN_DIR / "certidao_trabalhista/case_001.json").read_text())
        expected = case["expected_output"]
        task = load_task(TASKS_DIR / "extraction/certidao_trabalhista_extraction.yaml")
        task.expected = expected

        bad = copy.deepcopy(expected)
        bad["resultado"] = "positiva"
        result = run_task(task, bad)

        assert not result.passed
        resultado_grader = next(g for g in result.grader_results if g.field == "resultado")
        assert not resultado_grader.passed

    def test_missing_critical_field_fails(self) -> None:
        case = json.loads((GOLDEN_DIR / "cnd/case_001.json").read_text())
        expected = case["expected_output"]
        task = load_task(TASKS_DIR / "extraction/cnd_extraction.yaml")
        task.expected = expected

        bad = copy.deepcopy(expected)
        del bad["status"]
        result = run_task(task, bad)

        assert not result.passed

    def test_null_validade_matches_null(self) -> None:
        case = json.loads((GOLDEN_DIR / "certidao_trabalhista/case_001.json").read_text())
        expected = case["expected_output"]
        assert expected["validade"] is None

        task = load_task(TASKS_DIR / "extraction/certidao_trabalhista_extraction.yaml")
        task.expected = expected
        result = run_task(task, expected)

        validade_grader = next(g for g in result.grader_results if g.field == "validade")
        assert validade_grader.passed
        assert validade_grader.score == 1.0


class TestGoldenSetAwareRunner:
    def test_self_eval_extraction_all_pass(self) -> None:
        from gbr_eval.harness.runner import run_suite_with_golden

        run = run_suite_with_golden(
            TASKS_DIR, GOLDEN_DIR, self_eval=True,
        )
        extraction_results = [
            r for r in run.task_results
            if r.task_id.startswith("extraction.") and r.task_id != "extraction.balanco.fields"
        ]
        assert len(extraction_results) == 5
        for r in extraction_results:
            assert r.passed, f"{r.task_id} failed with score={r.score}"
            assert r.score == 1.0

    def test_load_golden_cases_returns_all(self) -> None:
        from gbr_eval.harness.runner import load_golden_cases

        cases = load_golden_cases(GOLDEN_DIR, "certidao_trabalhista")
        assert len(cases) == 8
        assert all("expected_output" in c for c in cases)

    def test_load_golden_cases_seed_only(self) -> None:
        from gbr_eval.harness.runner import load_golden_cases

        cases = load_golden_cases(GOLDEN_DIR, "certidao_trabalhista", tags=["seed"])
        assert len(cases) == 5
        assert all("seed" in c.get("tags", []) for c in cases)

    def test_load_golden_cases_missing_type(self) -> None:
        from gbr_eval.harness.runner import load_golden_cases

        cases = load_golden_cases(GOLDEN_DIR, "nonexistent_type")
        assert cases == []
