"""Tests for engineering-layer graders (pattern_required, pattern_forbidden, convention_check)."""

# Ensure graders are registered
import gbr_eval.graders.engineering  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

code_with_tenant = """
from app.db import get_session

def list_users(tenant_id: str):
    return db.query(User).filter(User.tenant_id == tenant_id).all()
"""

code_without_tenant = """
from app.db import get_session

def list_users():
    return db.query(User).all()
"""

code_with_hardcoded_value = """
from decimal import Decimal

def get_plan_price():
    return Decimal("99.90")

ITAU_TENANT_ID = "itau-prod-001"
"""

code_with_import = """
import os
import re
from pathlib import Path

def parse(content: str) -> dict:
    return {}
"""


# ---------------------------------------------------------------------------
# pattern_required
# ---------------------------------------------------------------------------


class TestPatternRequired:
    def test_pattern_required_found(self):
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": r"tenant_id"},
        )
        result = grade("pattern_required", {"content": code_with_tenant}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_pattern_required_missing(self):
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": r"tenant_id"},
        )
        result = grade("pattern_required", {"content": code_without_tenant}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "tenant_id" in result.details

    def test_pattern_required_no_pattern_config(self):
        spec = GraderSpec(
            type="pattern_required",
            config={},
        )
        result = grade("pattern_required", {"content": code_with_tenant}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "No pattern" in result.details

    def test_pattern_required_empty_content(self):
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": r"tenant_id"},
        )
        result = grade("pattern_required", {"content": ""}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_pattern_required_regex_match(self):
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": r"\bimport\s+\w+"},
        )
        result = grade("pattern_required", {"content": code_with_import}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "matches" in result.details


# ---------------------------------------------------------------------------
# pattern_forbidden
# ---------------------------------------------------------------------------


class TestPatternForbidden:
    def test_pattern_forbidden_absent(self):
        spec = GraderSpec(
            type="pattern_forbidden",
            config={"pattern": r"ITAU_TENANT_ID\s*="},
        )
        result = grade("pattern_forbidden", {"content": code_with_tenant}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_pattern_forbidden_present(self):
        spec = GraderSpec(
            type="pattern_forbidden",
            config={"pattern": r"ITAU_TENANT_ID\s*="},
        )
        result = grade("pattern_forbidden", {"content": code_with_hardcoded_value}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_pattern_forbidden_multiple_matches(self):
        repeated = "ITAU_TENANT_ID = 'a'\nITAU_TENANT_ID = 'b'\nITAU_TENANT_ID = 'c'\n"
        spec = GraderSpec(
            type="pattern_forbidden",
            config={"pattern": r"ITAU_TENANT_ID\s*="},
        )
        result = grade("pattern_forbidden", {"content": repeated}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "3" in result.details


# ---------------------------------------------------------------------------
# convention_check
# ---------------------------------------------------------------------------


class TestConventionCheck:
    def test_convention_all_rules_pass(self):
        """All required patterns present and all forbidden patterns absent → pass."""
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {"pattern": r"tenant_id", "type": "required", "description": "tenant_id filter"},
                    {"pattern": r"get_session", "type": "required", "description": "session helper"},
                    {"pattern": r"SELECT \*", "type": "forbidden", "description": "raw SELECT *"},
                ]
            },
        )
        result = grade("convention_check", {"content": code_with_tenant}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "All" in result.details

    def test_convention_required_missing(self):
        """A required pattern that is absent → fail."""
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {"pattern": r"tenant_id", "type": "required", "description": "tenant_id filter"},
                ]
            },
        )
        result = grade("convention_check", {"content": code_without_tenant}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "MISSING" in result.details

    def test_convention_forbidden_found(self):
        """A forbidden pattern that is present → fail."""
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {
                        "pattern": r"ITAU_TENANT_ID\s*=",
                        "type": "forbidden",
                        "description": "hardcoded tenant id",
                    },
                ]
            },
        )
        result = grade("convention_check", {"content": code_with_hardcoded_value}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "FOUND" in result.details

    def test_convention_mixed_violations(self):
        """Some rules pass, some fail → score reflects ratio of passing rules."""
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {"pattern": r"tenant_id", "type": "required", "description": "tenant_id filter"},
                    {"pattern": r"get_session", "type": "required", "description": "session helper"},
                    {
                        "pattern": r"ITAU_TENANT_ID\s*=",
                        "type": "forbidden",
                        "description": "hardcoded tenant id",
                    },
                ]
            },
        )
        # code_with_hardcoded_value has no tenant_id (missing required) and has ITAU_TENANT_ID (forbidden present)
        # → 2 violations out of 3 rules → score = max(0, 1 - 2/3) ≈ 0.33
        result = grade("convention_check", {"content": code_with_hardcoded_value}, {}, spec)
        assert not result.passed
        assert result.score < 0.5

    def test_convention_empty_rules(self):
        """Empty rules list → fail with descriptive message."""
        spec = GraderSpec(
            type="convention_check",
            config={"rules": []},
        )
        result = grade("convention_check", {"content": code_with_tenant}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "No rules" in result.details

    def test_convention_partial_score(self):
        """2 of 3 rules pass → score approximately 0.67."""
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {"pattern": r"tenant_id", "type": "required", "description": "tenant_id filter"},
                    {"pattern": r"get_session", "type": "required", "description": "session helper"},
                    {"pattern": r"audit_log", "type": "required", "description": "audit log call"},
                ]
            },
        )
        # code_with_tenant has tenant_id and get_session, but not audit_log → 1 violation / 3 rules
        # score = max(0, 1 - 1/3) ≈ 0.667
        result = grade("convention_check", {"content": code_with_tenant}, {}, spec)
        assert not result.passed
        assert abs(result.score - (2 / 3)) < 0.01


# ---------------------------------------------------------------------------
# pattern_required edge cases
# ---------------------------------------------------------------------------


class TestPatternRequiredEdgeCases:
    def test_pattern_required_invalid_regex(self):
        """Invalid regex pattern returns fail with 'Invalid regex' in details."""
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": "[unclosed"},
        )
        result = grade("pattern_required", {"content": "some content"}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "Invalid regex" in result.details

    def test_pattern_required_non_string_content(self):
        """Non-string content is coerced to str before matching."""
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": r"42"},
        )
        result = grade("pattern_required", {"content": 42}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_pattern_required_pattern_too_long(self):
        """Pattern longer than 1000 chars returns fail."""
        long_pattern = "a" * 1001
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": long_pattern},
        )
        result = grade("pattern_required", {"content": "anything"}, {}, spec)
        assert not result.passed
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# convention_check edge cases
# ---------------------------------------------------------------------------


class TestConventionCheckEdgeCases:
    def test_convention_check_invalid_regex_in_rule(self):
        """A rule with an invalid regex adds an ERROR violation and does not crash."""
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {"pattern": "[bad", "type": "required", "description": "broken rule"},
                    {"pattern": r"tenant_id", "type": "required", "description": "tenant filter"},
                ]
            },
        )
        result = grade("convention_check", {"content": code_with_tenant}, {}, spec)
        assert not result.passed
        assert "ERROR" in result.details


# ---------------------------------------------------------------------------
# _MAX_INPUT_LEN truncation (N8)
# ---------------------------------------------------------------------------


class TestPatternRequiredTruncation:
    def test_pattern_required_truncates_long_content(self):
        """Content longer than _MAX_INPUT_LEN is truncated; pattern past the limit is not found."""
        # FINDME starts at position 100_001 — beyond the 100_000-char slice
        long_content = "x" * 100_001 + "FINDME"
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": "FINDME", "file_key": "content"},
        )
        result = grade("pattern_required", {"content": long_content}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_pattern_required_finds_within_limit(self):
        """Content within _MAX_INPUT_LEN is fully searchable."""
        # FINDME ends at position 99_996 — well inside the 100_000-char slice
        content = "x" * 99_990 + "FINDME"
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": "FINDME", "file_key": "content"},
        )
        result = grade("pattern_required", {"content": content}, {}, spec)
        assert result.passed
        assert result.score == 1.0


# ---------------------------------------------------------------------------
# Catastrophic regex (ReDoS) guard (H6)
# ---------------------------------------------------------------------------


class TestCatastrophicRegexGuard:
    def test_pattern_required_rejects_catastrophic(self):
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": "(a+)+$"},
        )
        result = grade("pattern_required", {"content": "aaa"}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_pattern_forbidden_rejects_catastrophic(self):
        spec = GraderSpec(
            type="pattern_forbidden",
            config={"pattern": "(x+)+y"},
        )
        result = grade("pattern_forbidden", {"content": "xxx"}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_convention_check_rejects_catastrophic_rule(self):
        spec = GraderSpec(
            type="convention_check",
            config={
                "rules": [
                    {"pattern": "(a+)+$", "type": "required", "description": "bad rule"},
                    {"pattern": r"tenant_id", "type": "required", "description": "good rule"},
                ]
            },
        )
        result = grade("convention_check", {"content": code_with_tenant}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_safe_pattern_passes_guard(self):
        spec = GraderSpec(
            type="pattern_required",
            config={"pattern": r"tenant_id\s*=="},
        )
        result = grade("pattern_required", {"content": code_with_tenant}, {}, spec)
        assert result.passed
