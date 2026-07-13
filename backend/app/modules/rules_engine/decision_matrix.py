"""Governed decision matrix and band derivation (PRD 6.7).

The matrix yields a *default* recommended action from three bands (funding
merit, strategic alignment, evidence strength). It is advisory input to the
committee, never an autonomous decision (PRD 12.2).
"""

from __future__ import annotations

from app.domain.enums import Band, DecisionState, EvidenceStrength

# Thresholds on the 0-10 index scale for banding. Configurable seed values.
MERIT_HIGH_THRESHOLD = 6.0
ALIGNMENT_HIGH_THRESHOLD = 6.0
EVIDENCE_STRONG_THRESHOLD = 6.0


def band(value: float, high_threshold: float) -> Band:
    return Band.HIGH if value >= high_threshold else Band.LOW


def evidence_strength(evi_value: float, threshold: float = EVIDENCE_STRONG_THRESHOLD) -> EvidenceStrength:
    return EvidenceStrength.STRONG if evi_value >= threshold else EvidenceStrength.WEAK


# PRD 6.7 decision matrix, keyed by (merit, alignment, evidence).
# ``None`` for evidence means "Any".
_MATRIX: dict[tuple[Band, Band, EvidenceStrength | None], tuple[DecisionState, str]] = {
    (Band.HIGH, Band.HIGH, EvidenceStrength.STRONG): (
        DecisionState.FUND,
        "Priority funding candidate",
    ),
    (Band.HIGH, Band.LOW, EvidenceStrength.STRONG): (
        DecisionState.FUND_WITH_CONDITIONS,
        "Fund only where programme mandate permits",
    ),
    (Band.LOW, Band.HIGH, EvidenceStrength.STRONG): (
        DecisionState.DEVELOP,
        "Develop, redesign or conditional support",
    ),
    (Band.HIGH, Band.HIGH, EvidenceStrength.WEAK): (
        DecisionState.DEFER,
        "Defer or fund with verification conditions",
    ),
}


def recommend(
    merit: float,
    alignment: float,
    evi: float,
) -> tuple[DecisionState, str]:
    """Return the matrix's default (state, note) for the given index values.

    The last matrix row — Low merit, Low alignment, Any evidence -> Decline —
    is applied as the fallthrough.
    """

    m = band(merit, MERIT_HIGH_THRESHOLD)
    a = band(alignment, ALIGNMENT_HIGH_THRESHOLD)
    e = evidence_strength(evi)

    if (m, a, e) in _MATRIX:
        return _MATRIX[(m, a, e)]

    if m == Band.LOW and a == Band.LOW:
        return DecisionState.DECLINE, "Decline"

    # High merit + Low alignment + Weak evidence, and Low+High+Weak: not
    # enumerated in the PRD matrix -> defer for evidence rather than auto-decline.
    return DecisionState.DEFER, "Material evidence missing; defer for verification"
