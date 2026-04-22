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


# ---------------------------------------------------------------------------
# decimal_usage grader
# ---------------------------------------------------------------------------

financial_code_with_decimal = '''
from decimal import Decimal

def calculate_fee(amount: Decimal) -> Decimal:
    markup = Decimal("0.05")
    return amount * markup
'''

financial_code_with_float = '''
def calculate_fee(amount: float) -> float:
    markup = 0.05
    return amount * markup
'''

financial_code_with_float_cast = '''
def process_payment(data: dict):
    price = float(data["price"])
    total = float(data["amount"]) * 1.1
'''

non_financial_code = '''
import os
def parse_config(path: str) -> dict:
    ratio: float = 0.5  # This float is fine - not financial
    return {"ratio": ratio}
'''

mixed_code_decimal_and_int = '''
from decimal import Decimal

def get_total(price: Decimal, quantity: int) -> Decimal:
    return price * quantity
'''

code_with_int_billing = '''
def emit_usage_event(search_element_id: str):
    quantity = 1  # Always 1 - no Decimal needed
    return {"quantity": quantity}
'''


class TestDecimalUsage:
    def test_decimal_usage_financial_with_decimal_passes(self):
        """Decimal used properly in financial code → pass."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": financial_code_with_decimal}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_decimal_usage_financial_with_float_fails(self):
        """float type annotation in financial code → fail."""
        # financial_code_with_float has `amount: float` but no financial term on the
        # same line. However it has `fee` in the function name which is a financial term,
        # and the function signature line contains `: float` — that triggers the
        # forbidden annotation pattern `:\s*float\b`.
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": financial_code_with_float}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "float" in result.details.lower()

    def test_decimal_usage_financial_with_float_cast_fails(self):
        """Explicit float() cast in financial code → fail."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": financial_code_with_float_cast}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "float" in result.details.lower()

    def test_decimal_usage_non_financial_skipped(self):
        """Non-financial code → auto-pass (skipped)."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": non_financial_code}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "skipped" in result.details.lower()

    def test_decimal_usage_skip_disabled_non_financial_float_annotation_fails(self):
        """skip_if_no_context=False: non-financial file with float annotation still checked."""
        spec = GraderSpec(type="decimal_usage", config={"skip_if_no_context": False})
        result = grade("decimal_usage", {"content": non_financial_code}, {}, spec)
        # non_financial_code has `ratio: float` → forbidden annotation fires
        assert not result.passed
        assert result.score == 0.0

    def test_decimal_usage_mixed_decimal_and_int_passes(self):
        """Decimal + int in financial code → pass."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": mixed_code_decimal_and_int}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_decimal_usage_int_only_billing_passes(self):
        """int quantity, no float, no Decimal, but financial term (billing) → pass."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": code_with_int_billing}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_decimal_usage_empty_content(self):
        """Empty content → no financial context → auto-pass."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": ""}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "skipped" in result.details.lower()

    def test_decimal_usage_custom_financial_terms(self):
        """Override financial_terms: only match 'tarifa' — non-matching code auto-passes."""
        spec = GraderSpec(
            type="decimal_usage",
            config={"financial_terms": r"tarifa"},
        )
        # financial_code_with_float uses 'fee' but not 'tarifa' → auto-pass
        result = grade("decimal_usage", {"content": financial_code_with_float}, {}, spec)
        assert result.passed
        assert "skipped" in result.details.lower()

    def test_decimal_usage_custom_financial_terms_hits(self):
        """Override financial_terms: matching 'tarifa' triggers check and float fails."""
        tarifa_float_code = """
def calcular_tarifa(valor: float) -> float:
    return valor * 0.02
"""
        spec = GraderSpec(
            type="decimal_usage",
            config={"financial_terms": r"tarifa"},
        )
        result = grade("decimal_usage", {"content": tarifa_float_code}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_decimal_usage_catastrophic_regex_rejected_financial_terms(self):
        """Catastrophic regex in financial_terms → fail with rejection message."""
        spec = GraderSpec(
            type="decimal_usage",
            config={"financial_terms": "(a+)+$"},
        )
        result = grade("decimal_usage", {"content": "some content"}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_decimal_usage_catastrophic_regex_rejected_forbidden_patterns(self):
        """Catastrophic regex in forbidden_float_patterns → fail with rejection message."""
        spec = GraderSpec(
            type="decimal_usage",
            config={
                "financial_terms": r"price",
                "forbidden_float_patterns": ["(x+)+y"],
            },
        )
        result = grade("decimal_usage", {"content": "price = 10"}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_decimal_usage_no_pattern_in_config_uses_defaults(self):
        """No explicit config → uses all defaults, financial code with Decimal passes."""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": financial_code_with_decimal}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_decimal_usage_float_literal_on_financial_line_fails(self):
        """Float literal assignment on a line that also contains a financial term → fail."""
        code = "markup = 0.05  # fee calculation\n"
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": code}, {}, spec)
        assert not result.passed
        assert "Float literal" in result.details

    def test_decimal_usage_float_literal_on_non_financial_line_passes(self):
        """Float literal assignment on a line without a financial term is allowed (with financial context elsewhere)."""
        code = """
from decimal import Decimal

RATIO_MULTIPLIER = 1.0  # generic ratio — no financial term on this line

def get_amount(value: Decimal) -> Decimal:
    return value * Decimal("1.1")
"""
        spec = GraderSpec(type="decimal_usage", config={})
        result = grade("decimal_usage", {"content": code}, {}, spec)
        assert result.passed
        assert result.score == 1.0


# ---------------------------------------------------------------------------
# pattern_forbidden context filtering (exclude_context / require_context)
# ---------------------------------------------------------------------------


class TestPatternForbiddenContextFiltering:
    def test_exclude_context_skips_matching_lines(self):
        """err.message inside console.error() is safe logging — should NOT be flagged."""
        code = 'console.error("Failed:", err.message);\n'
        spec = GraderSpec(
            type="pattern_forbidden",
            config={
                "pattern": r"err\.message",
                "exclude_context": r"console\.(error|warn|log)",
            },
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_exclude_context_flags_non_matching_lines(self):
        """err.message NOT inside console.error() should still be flagged."""
        code = 'return NextResponse.json({ error: err.message });\n'
        spec = GraderSpec(
            type="pattern_forbidden",
            config={
                "pattern": r"err\.message",
                "exclude_context": r"console\.(error|warn|log)",
            },
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_require_context_only_flags_matching_lines(self):
        """err.message should only be flagged when on a line with NextResponse.json."""
        code = (
            'console.error("Fail:", err.message);\n'
            'return NextResponse.json({ error: err.message });\n'
        )
        spec = GraderSpec(
            type="pattern_forbidden",
            config={
                "pattern": r"err\.message",
                "require_context": r"NextResponse\.json",
            },
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert not result.passed
        assert "1 matches" in result.details

    def test_require_context_passes_when_no_context_match(self):
        """err.message on lines without NextResponse.json should pass."""
        code = 'console.error("Fail:", err.message);\n'
        spec = GraderSpec(
            type="pattern_forbidden",
            config={
                "pattern": r"err\.message",
                "require_context": r"NextResponse\.json",
            },
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert result.passed

    def test_both_exclude_and_require_context(self):
        """Both filters can be combined."""
        code = (
            'console.error("Fail:", err.message);\n'                      # excluded
            'return NextResponse.json({ error: err.message });\n'          # flagged
            'const msg = err.message;\n'                                   # no require_context
        )
        spec = GraderSpec(
            type="pattern_forbidden",
            config={
                "pattern": r"err\.message",
                "exclude_context": r"console\.(error|warn|log)",
                "require_context": r"NextResponse\.json|\.json\(",
            },
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert not result.passed
        assert "1 matches" in result.details

    def test_no_context_filters_backward_compatible(self):
        """Without context filters, behavior is identical to before."""
        code = 'err.message appears here\n'
        spec = GraderSpec(
            type="pattern_forbidden",
            config={"pattern": r"err\.message"},
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert not result.passed

    def test_context_filters_with_no_matches_at_all(self):
        """Pattern not present at all — passes regardless of context filters."""
        code = 'clean code with no issues\n'
        spec = GraderSpec(
            type="pattern_forbidden",
            config={
                "pattern": r"err\.message",
                "exclude_context": r"console\.",
                "require_context": r"NextResponse",
            },
        )
        result = grade("pattern_forbidden", {"content": code}, {}, spec)
        assert result.passed


# ---------------------------------------------------------------------------
# pattern_required context filtering
# ---------------------------------------------------------------------------


class TestPatternRequiredContextFiltering:
    def test_require_context_narrows_matches(self):
        """Only count pattern matches on lines also matching require_context."""
        code = (
            'import { useState } from "react";\n'
            'const [x, setX] = useState(0);\n'
            'let y = 42;\n'
        )
        spec = GraderSpec(
            type="pattern_required",
            config={
                "pattern": r"useState",
                "require_context": r"const\s+\[",
            },
        )
        result = grade("pattern_required", {"content": code}, {}, spec)
        assert result.passed
        assert "1 matches" in result.details

    def test_exclude_context_removes_matches(self):
        """Exclude pattern matches on lines matching exclude_context."""
        code = (
            '// useState import\n'
            'import { useState } from "react";\n'
        )
        spec = GraderSpec(
            type="pattern_required",
            config={
                "pattern": r"useState",
                "exclude_context": r"^import\s",
            },
        )
        result = grade("pattern_required", {"content": code}, {}, spec)
        # "useState" on comment line survives, import line excluded
        assert result.passed
