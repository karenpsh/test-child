"""Tests for the deterministic index calculations (PRD 6, acceptance #6)."""

from __future__ import annotations

from app.domain.enums import EvidenceState, LensType
from app.domain.methodology import default_methodology
from app.domain.models import Claim, DimensionScore
from app.modules.rules_engine.indices import (
    compute_evi,
    compute_sai,
    compute_ssai,
    compute_ssei,
)


def _full_sai_scores(value: float) -> list[DimensionScore]:
    return [DimensionScore(dimension=d, score=value) for d in default_methodology().sai_weights]


def test_sai_all_tens_is_ten():
    m = default_methodology()
    result = compute_sai(_full_sai_scores(10.0), m)
    assert result.lens is LensType.SAI
    assert result.value == 10.0
    assert result.missing_dimensions == []


def test_sai_weighted_average():
    m = default_methodology()
    # Technical (25%) at 8, everything else at 4.
    scores = [
        DimensionScore(dimension="technical_delivery_credibility", score=8.0),
        DimensionScore(dimension="commercial_adoption_readiness", score=4.0),
        DimensionScore(dimension="strategic_programme_fit", score=4.0),
        DimensionScore(dimension="financial_stewardship", score=4.0),
        DimensionScore(dimension="execution_capacity", score=4.0),
        DimensionScore(dimension="public_value_outcomes", score=4.0),
    ]
    result = compute_sai(scores, m)
    # 0.25*8 + 0.75*4 = 2 + 3 = 5
    assert result.value == 5.0


def test_missing_dimensions_reported_and_not_inflated():
    m = default_methodology()
    scores = [DimensionScore(dimension="technical_delivery_credibility", score=10.0)]
    result = compute_sai(scores, m)
    # Only 25% weight present -> 2.5, and five dimensions reported missing.
    assert result.value == 2.5
    assert len(result.missing_dimensions) == 5


def test_ssai_and_ssei_full_marks():
    m = default_methodology()
    ssai = compute_ssai([DimensionScore(dimension=d, score=10) for d in m.ssai_weights], m)
    ssei = compute_ssei([DimensionScore(dimension=d, score=10) for d in m.ssei_weights], m)
    assert ssai.value == 10.0
    assert round(ssei.value, 4) == 10.0


def test_evi_mean_confidence_on_ten_scale():
    m = default_methodology()
    claims = [
        Claim(text="verified", evidence_state=EvidenceState.INDEPENDENTLY_VERIFIED),  # 1.0
        Claim(text="declared", evidence_state=EvidenceState.APPLICANT_DECLARATION_ONLY),  # 0.3
    ]
    result = compute_evi(claims, m)
    # mean(1.0, 0.3) = 0.65 -> 6.5 on the 0-10 scale
    assert result.value == 6.5


def test_evi_contradicted_claim_scores_zero():
    m = default_methodology()
    claims = [
        Claim(
            text="contradicted",
            evidence_state=EvidenceState.INDEPENDENTLY_VERIFIED,
            contradicted=True,
        )
    ]
    result = compute_evi(claims, m)
    assert result.value == 0.0


def test_evi_no_claims():
    result = compute_evi([], default_methodology())
    assert result.value == 0.0
    assert result.missing_dimensions == ["no_claims"]
