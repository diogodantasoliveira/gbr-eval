"""Tests for calibration / inter-annotator agreement."""

import pytest

from gbr_eval.calibration.iaa import cohens_kappa


class TestCohensKappa:
    def test_perfect_agreement(self):
        labels = ["pass", "fail", "pass", "pass", "fail"]
        result = cohens_kappa(labels, labels)
        assert result.kappa == 1.0
        assert result.calibrated is True
        assert result.interpretation == "almost_perfect"

    def test_no_agreement(self):
        a = ["pass", "pass", "pass", "pass"]
        b = ["fail", "fail", "fail", "fail"]
        result = cohens_kappa(a, b)
        assert result.kappa <= 0
        assert result.observed_agreement == 0.0
        assert result.calibrated is False

    def test_moderate_agreement(self):
        a = ["pass", "fail", "pass", "fail", "pass", "fail", "pass", "fail", "pass", "pass"]
        b = ["pass", "fail", "pass", "pass", "pass", "fail", "fail", "fail", "pass", "pass"]
        result = cohens_kappa(a, b)
        assert 0.0 < result.kappa < 1.0

    def test_empty_lists(self):
        result = cohens_kappa([], [])
        assert result.n_items == 0
        assert result.calibrated is False

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="Length mismatch"):
            cohens_kappa(["a", "b"], ["a"])

    def test_custom_threshold(self):
        a = ["pass", "fail", "pass", "fail", "pass"]
        b = ["pass", "fail", "pass", "pass", "pass"]
        result_strict = cohens_kappa(a, b, threshold=0.90)
        result_lenient = cohens_kappa(a, b, threshold=0.30)
        assert result_strict.calibrated is False or result_lenient.calibrated is True

    def test_interpretation_labels(self):
        labels = ["a", "b", "a", "b", "a"]
        result = cohens_kappa(labels, labels)
        assert result.interpretation == "almost_perfect"
