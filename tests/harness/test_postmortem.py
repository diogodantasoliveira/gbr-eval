"""Tests for the PostMortem model."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from gbr_eval.harness.models import PostMortem


class TestPostMortem:
    def test_serialization_roundtrip(self):
        pm = PostMortem(
            what="extraction.cpf score dropped below 0.95",
            root_cause="prompt regression in v2.3",
            impact="3 gate failures in last 24h",
            fix="reverted prompt to v2.2",
            prevention="add canary test for CPF extraction",
            created_by="diogo@garantiabr.com",
        )

        json_str = pm.model_dump_json()
        restored = PostMortem.model_validate_json(json_str)

        assert restored.what == pm.what
        assert restored.root_cause == pm.root_cause
        assert restored.impact == pm.impact
        assert restored.fix == pm.fix
        assert restored.prevention == pm.prevention
        assert restored.created_by == pm.created_by

    def test_required_fields(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PostMortem(
                what="something broke",
                root_cause="unknown",
            )  # type: ignore[call-arg]

    def test_created_at_default(self):
        before = datetime.now(UTC)
        pm = PostMortem(
            what="test",
            root_cause="test",
            impact="test",
            fix="test",
            prevention="test",
            created_by="test@test.com",
        )
        after = datetime.now(UTC)

        assert before <= pm.created_at <= after

    def test_created_at_in_json(self):
        pm = PostMortem(
            what="test",
            root_cause="test",
            impact="test",
            fix="test",
            prevention="test",
            created_by="test@test.com",
        )

        data = json.loads(pm.model_dump_json())

        assert "created_at" in data
        assert isinstance(data["created_at"], str)
