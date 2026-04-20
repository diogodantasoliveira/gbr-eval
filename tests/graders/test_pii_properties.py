"""Property-based tests for PII sanitization (Hypothesis)."""
from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from gbr_eval.graders.model_judge import _sanitize_pii, _sanitize_pii_str


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
