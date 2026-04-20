"""Property-based tests for PII sanitization (Hypothesis)."""
from __future__ import annotations

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from gbr_eval.graders.model_judge import _PII_PATTERNS, _sanitize_pii, _sanitize_pii_str


class TestPiiStringProperties:
    @settings(max_examples=50)
    @given(st.from_regex(r"\d{3}\.\d{3}\.\d{3}-\d{2}", fullmatch=True))
    def test_formatted_cpf_always_redacted(self, cpf: str) -> None:
        result = _sanitize_pii_str(cpf)
        assert result != cpf  # must be changed

    @settings(max_examples=50)
    @given(st.from_regex(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", fullmatch=True))
    def test_formatted_cnpj_always_redacted(self, cnpj: str) -> None:
        result = _sanitize_pii_str(cnpj)
        assert result != cnpj  # must be changed

    @settings(max_examples=50)
    @given(st.text(min_size=0, max_size=200))
    def test_sanitize_never_crashes(self, text: str) -> None:
        result = _sanitize_pii_str(text)
        assert isinstance(result, str)

    @settings(max_examples=50)
    @given(st.text(min_size=0, max_size=200))
    def test_sanitize_is_idempotent(self, text: str) -> None:
        once = _sanitize_pii_str(text)
        twice = _sanitize_pii_str(once)
        assert once == twice


class TestPiiDictProperties:
    @settings(max_examples=50)
    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(st.text(max_size=50), st.integers(), st.none(), st.floats(allow_nan=False)),
            max_size=5,
        )
    )
    def test_sanitize_dict_never_crashes(self, data: dict) -> None:  # type: ignore[type-arg]
        result = _sanitize_pii(data)
        assert isinstance(result, dict)

    @settings(max_examples=50)
    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(st.text(max_size=50), st.integers(), st.none()),
            max_size=5,
        )
    )
    def test_sanitize_dict_preserves_keys(self, data: dict) -> None:  # type: ignore[type-arg]
        result = _sanitize_pii(data)
        assert set(result.keys()) == set(data.keys())

    @settings(max_examples=50)
    @given(
        st.recursive(
            st.one_of(st.text(max_size=20), st.integers(), st.none()),
            lambda children: st.dictionaries(
                keys=st.text(min_size=1, max_size=5),
                values=children,
                max_size=3,
            ),
            max_leaves=10,
        )
    )
    def test_nested_sanitize_never_crashes(self, data: object) -> None:
        if isinstance(data, dict):
            result = _sanitize_pii(data)
            assert isinstance(result, dict)


def test_pii_pattern_categories_documented() -> None:
    """Ensure all PII pattern categories are accounted for.

    Cross-reference with gbr-eval-frontend/src/lib/pii/patterns.ts.
    Each entry in expected_categories must have at least one matching pattern
    in _PII_PATTERNS. If a new category is added to either side, update both
    Python (_PII_PATTERNS in model_judge.py) and TypeScript (patterns.ts).

    TypeScript-only categories NOT expected here (by design):
      - Address: structured JSON fields don't need street-name regex
      - BRL_currency: currency values are business data, not PII for grading
    """
    # Canonical sample values per category — must be fully consumed by a pattern
    category_samples: dict[str, str] = {
        "cpf": "123.456.789-09",
        "cnpj": "12.345.678/0001-99",
        "email": "user@example.com",
        "phone": "(11) 91234-5678",
        "rg": "12.345.678-9",
        "pis_pasep": "123.45678.90-1",
        "cep": "01310-100",
    }

    expected_categories = set(category_samples)

    covered: set[str] = set()
    for category, sample in category_samples.items():
        for pattern, _replacement in _PII_PATTERNS:
            if re.search(pattern, sample):
                covered.add(category)
                break

    missing = expected_categories - covered
    assert not missing, (
        f"PII categories with no matching pattern: {sorted(missing)}. "
        "Add the pattern to _PII_PATTERNS in model_judge.py and update "
        "gbr-eval-frontend/src/lib/pii/patterns.ts if applicable."
    )
