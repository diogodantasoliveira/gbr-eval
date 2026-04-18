"""Inter-annotator agreement — Cohen's kappa for calibration tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgreementResult:
    kappa: float
    observed_agreement: float
    expected_agreement: float
    n_items: int
    calibrated: bool

    @property
    def interpretation(self) -> str:
        if self.kappa >= 0.81:
            return "almost_perfect"
        if self.kappa >= 0.61:
            return "substantial"
        if self.kappa >= 0.41:
            return "moderate"
        if self.kappa >= 0.21:
            return "fair"
        if self.kappa >= 0.0:
            return "slight"
        return "poor"


def cohens_kappa(
    annotator_a: list[str],
    annotator_b: list[str],
    threshold: float = 0.75,
) -> AgreementResult:
    """Compute Cohen's kappa between two annotators.

    Args:
        annotator_a: Labels from annotator A (e.g., human/CLO).
        annotator_b: Labels from annotator B (e.g., grader or Claude).
        threshold: Minimum kappa to consider calibrated.
    """
    if len(annotator_a) != len(annotator_b):
        raise ValueError(f"Length mismatch: {len(annotator_a)} vs {len(annotator_b)}")

    n = len(annotator_a)
    if n == 0:
        return AgreementResult(kappa=0.0, observed_agreement=0.0, expected_agreement=0.0, n_items=0, calibrated=False)

    labels = sorted(set(annotator_a) | set(annotator_b))

    observed = sum(a == b for a, b in zip(annotator_a, annotator_b)) / n

    expected = 0.0
    for label in labels:
        p_a = annotator_a.count(label) / n
        p_b = annotator_b.count(label) / n
        expected += p_a * p_b

    if expected == 1.0:
        kappa = 1.0
    else:
        kappa = (observed - expected) / (1.0 - expected)

    return AgreementResult(
        kappa=kappa,
        observed_agreement=observed,
        expected_agreement=expected,
        n_items=n,
        calibrated=kappa >= threshold,
    )
