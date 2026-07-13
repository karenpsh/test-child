"""Deterministic index calculations: SAI, SSAI, SSEI, EVI (PRD 6).

These functions are pure and reproducible from stored inputs (acceptance
criterion 6). Generative AI must never touch them (PRD 10, 12.2). Scores are
on a 0-10 scale; indices are returned on the same 0-10 scale for consistency
across lenses.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import LensType
from app.domain.methodology import MethodologyVersion
from app.domain.models import Claim, DimensionScore


class IndexResult(BaseModel):
    """A computed index with its per-dimension contributions for transparency."""

    lens: LensType
    value: float
    contributions: dict[str, float]
    methodology_version: str
    missing_dimensions: list[str]


def _weighted_index(
    lens: LensType,
    scores: list[DimensionScore],
    weights: dict[str, float],
    methodology_version: str,
) -> IndexResult:
    """Weighted sum of dimension scores. Missing dimensions score 0 and are
    reported so incomplete submissions are visible rather than silently
    inflating the result."""

    by_dim = {s.dimension: s.score for s in scores}
    contributions: dict[str, float] = {}
    total = 0.0
    missing: list[str] = []
    for dim, weight in weights.items():
        score = by_dim.get(dim)
        if score is None:
            missing.append(dim)
            score = 0.0
        contribution = weight * score
        contributions[dim] = round(contribution, 4)
        total += contribution
    return IndexResult(
        lens=lens,
        value=round(total, 4),
        contributions=contributions,
        methodology_version=methodology_version,
        missing_dimensions=missing,
    )


def compute_sai(scores: list[DimensionScore], methodology: MethodologyVersion) -> IndexResult:
    """SAI. Sarawak Allocation Index (PRD 6.1)."""

    return _weighted_index(LensType.SAI, scores, methodology.sai_weights, methodology.version)


def compute_ssai(scores: list[DimensionScore], methodology: MethodologyVersion) -> IndexResult:
    """SSAI. Sarawak Strategic Alignment Index (PRD 6.2)."""

    return _weighted_index(LensType.SSAI, scores, methodology.ssai_weights, methodology.version)


def compute_ssei(scores: list[DimensionScore], methodology: MethodologyVersion) -> IndexResult:
    """SSEI. Sarawak Sustainability and ESG Index (PRD 6.4)."""

    return _weighted_index(LensType.SSEI, scores, methodology.ssei_weights, methodology.version)


def compute_evi(claims: list[Claim], methodology: MethodologyVersion) -> IndexResult:
    """EVI. Evidence Veracity Index (PRD 6.6).

    EVI is the mean confidence across material claims, expressed on a 0-10
    scale. Per PRD 6.6 these confidence weights are *not* added into SAI/SSAI/
    SSEI; EVI is reported as a separate lens so weak evidence is visible rather
    than blended away. A contradicted claim contributes 0.
    """

    if not claims:
        return IndexResult(
            lens=LensType.EVI,
            value=0.0,
            contributions={},
            methodology_version=methodology.version,
            missing_dimensions=["no_claims"],
        )

    contributions: dict[str, float] = {}
    total = 0.0
    for claim in claims:
        state = claim.evidence_state
        confidence = 0.0 if claim.contradicted else methodology.evidence_confidence.get(state, 0.0)
        contributions[str(claim.id)] = round(confidence, 4)
        total += confidence
    mean_confidence = total / len(claims)  # 0..1
    return IndexResult(
        lens=LensType.EVI,
        value=round(mean_confidence * 10, 4),  # 0..10 scale
        contributions=contributions,
        methodology_version=methodology.version,
        missing_dimensions=[],
    )
