"""Rules Engine orchestration: indices + divergence + veto + publication block.

This service composes the deterministic primitives into a single evaluation
result for an application. It also enforces the publication block (PRD 13,
acceptance criteria 7 & 8): no approval state may be published while mandatory
evidence, assessor submissions, unresolved material divergence or confirmed
vetoes remain.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import DecisionState, ResolutionState
from app.domain.methodology import MethodologyVersion
from app.domain.models import Claim, DivergenceAlert, Scorecard, Veto
from app.modules.rules_engine import decision_matrix, divergence
from app.modules.rules_engine.indices import (
    IndexResult,
    compute_evi,
    compute_sai,
    compute_ssai,
    compute_ssei,
)

# Decision states that constitute "approval" and are therefore blockable.
APPROVAL_STATES = {DecisionState.FUND, DecisionState.FUND_WITH_CONDITIONS}


class PublicationBlock(BaseModel):
    reason: str
    detail: str


class EvaluationResult(BaseModel):
    """Everything the committee decision card needs (PRD 8.5)."""

    sai: IndexResult
    ssai: IndexResult
    ssei: IndexResult
    evi: IndexResult
    recommended_state: DecisionState
    recommendation_note: str
    divergence_alerts: list[DivergenceAlert]
    confirmed_vetoes: list[Veto]
    publication_blocks: list[PublicationBlock]

    @property
    def can_publish_approval(self) -> bool:
        return not self.publication_blocks


def _aggregate_dimension_scores(scorecards: list[Scorecard], lens) -> list:
    """Mean each dimension across submitted scorecards for a given lens."""

    from collections import defaultdict
    from statistics import fmean

    from app.domain.models import DimensionScore

    buckets: dict[str, list[float]] = defaultdict(list)
    for sc in scorecards:
        if sc.submitted and sc.lens == lens:
            for ds in sc.dimension_scores:
                buckets[ds.dimension].append(ds.score)
    return [DimensionScore(dimension=dim, score=fmean(vals)) for dim, vals in buckets.items()]


def evaluate(
    *,
    scorecards: list[Scorecard],
    claims: list[Claim],
    vetoes: list[Veto],
    methodology: MethodologyVersion,
    submission_threshold: int,
    open_divergence: list[DivergenceAlert] | None = None,
) -> EvaluationResult:
    """Run the full deterministic evaluation for one application."""

    from app.domain.enums import LensType

    sai = compute_sai(_aggregate_dimension_scores(scorecards, LensType.SAI), methodology)
    ssai = compute_ssai(_aggregate_dimension_scores(scorecards, LensType.SSAI), methodology)
    ssei = compute_ssei(_aggregate_dimension_scores(scorecards, LensType.SSEI), methodology)
    evi = compute_evi(claims, methodology)

    state, note = decision_matrix.recommend(sai.value, ssai.value, evi.value)

    alerts = divergence.detect_all(scorecards, methodology.individual_outlier_threshold)
    if open_divergence:
        alerts = alerts + open_divergence

    confirmed_vetoes = [v for v in vetoes if v.confirmed]

    blocks = _publication_blocks(
        scorecards=scorecards,
        claims=claims,
        alerts=alerts,
        confirmed_vetoes=confirmed_vetoes,
        recommended_state=state,
        submission_threshold=submission_threshold,
    )

    return EvaluationResult(
        sai=sai,
        ssai=ssai,
        ssei=ssei,
        evi=evi,
        recommended_state=state,
        recommendation_note=note,
        divergence_alerts=alerts,
        confirmed_vetoes=confirmed_vetoes,
        publication_blocks=blocks,
    )


def _publication_blocks(
    *,
    scorecards: list[Scorecard],
    claims: list[Claim],
    alerts: list[DivergenceAlert],
    confirmed_vetoes: list[Veto],
    recommended_state: DecisionState,
    submission_threshold: int,
) -> list[PublicationBlock]:
    """Return blocks that must be cleared before an approval may be published.

    Blocks only apply to approval states; a Decline/Disqualify is always
    publishable.
    """

    blocks: list[PublicationBlock] = []
    if recommended_state not in APPROVAL_STATES:
        return blocks

    submitted = [sc for sc in scorecards if sc.submitted]
    if len(submitted) < submission_threshold:
        blocks.append(
            PublicationBlock(
                reason="assessment_incomplete",
                detail=f"{len(submitted)}/{submission_threshold} required scorecards submitted.",
            )
        )

    unresolved = [
        a
        for a in alerts
        if a.resolution in (ResolutionState.UNRESOLVED, ResolutionState.ESCALATED)
    ]
    if unresolved:
        blocks.append(
            PublicationBlock(
                reason="material_divergence_unresolved",
                detail=f"{len(unresolved)} divergence alert(s) awaiting resolution.",
            )
        )

    if confirmed_vetoes:
        cats = ", ".join(sorted({v.category.value for v in confirmed_vetoes}))
        blocks.append(
            PublicationBlock(
                reason="confirmed_veto",
                detail=f"Confirmed veto(es): {cats}.",
            )
        )

    contradicted = [c for c in claims if c.contradicted]
    if contradicted:
        blocks.append(
            PublicationBlock(
                reason="contradicted_evidence",
                detail=f"{len(contradicted)} claim(s) flagged as contradicted.",
            )
        )

    return blocks
