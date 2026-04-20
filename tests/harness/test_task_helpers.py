"""Tests for task_with() composition helper."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gbr_eval.harness.models import (
    Category,
    GraderSpec,
    Layer,
    ScoringMode,
    Task,
    TaskInput,
    Tier,
)
from gbr_eval.harness.task_helpers import task_with


def _make_task(**kwargs: object) -> Task:
    defaults: dict[str, object] = {
        "task_id": "test.task_with",
        "category": Category.EXTRACTION,
        "component": "test",
        "layer": Layer.PRODUCT,
        "tier": Tier.GATE,
        "input": TaskInput(),
        "expected": {"cpf": "123.456.789-09"},
        "graders": [GraderSpec(type="exact_match", field="cpf", weight=3.0, required=True)],
        "scoring_mode": ScoringMode.WEIGHTED,
        "pass_threshold": 0.95,
    }
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


class TestTaskWith:
    def test_overrides_pass_threshold(self) -> None:
        original = _make_task()
        result = task_with(original, pass_threshold=0.80)
        assert result.pass_threshold == 0.80
        assert original.pass_threshold == 0.95

    def test_overrides_multiple_fields(self) -> None:
        result = task_with(_make_task(), pass_threshold=0.80, tenant_profile="itau")
        assert result.pass_threshold == 0.80
        assert result.tenant_profile == "itau"

    def test_invalid_threshold_raises(self) -> None:
        with pytest.raises(ValidationError):
            task_with(_make_task(), pass_threshold=1.5)

    def test_target_below_pass_raises(self) -> None:
        with pytest.raises(ValidationError, match="target_threshold"):
            task_with(_make_task(pass_threshold=0.90), target_threshold=0.50)

    def test_preserves_original(self) -> None:
        original = _make_task()
        _ = task_with(original, pass_threshold=0.50)
        assert original.pass_threshold == 0.95
        assert original.tenant_profile == "global"

    def test_deep_copies_graders(self) -> None:
        original = _make_task()
        new_graders = [GraderSpec(type="field_f1", field="nome", weight=1.0)]
        result = task_with(original, graders=new_graders)
        assert len(result.graders) == 1
        assert result.graders[0].type == "field_f1"
        assert len(original.graders) == 1
        assert original.graders[0].type == "exact_match"

    def test_empty_overrides_returns_copy(self) -> None:
        original = _make_task()
        copy = task_with(original)
        assert copy == original
        assert copy is not original

    def test_override_scoring_mode(self) -> None:
        result = task_with(_make_task(), scoring_mode=ScoringMode.BINARY)
        assert result.scoring_mode == ScoringMode.BINARY

    def test_task_with_epochs_override(self) -> None:
        """Overriding epochs via task_with must persist on the returned task."""
        result = task_with(_make_task(), epochs=5)
        assert result.epochs == 5

    def test_task_with_reducer_override(self) -> None:
        """Overriding reducers and primary_reducer via task_with must persist."""
        from gbr_eval.harness.models import ScoreReducer
        result = task_with(
            _make_task(),
            reducers=[ScoreReducer.MEDIAN, ScoreReducer.MEAN],
            primary_reducer=ScoreReducer.MEDIAN,
        )
        assert ScoreReducer.MEDIAN in result.reducers
        assert result.primary_reducer == ScoreReducer.MEDIAN
