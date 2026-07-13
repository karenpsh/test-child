"""Tests for publication blocks and veto enforcement (PRD 13, acceptance #7, #8)."""

from __future__ import annotations

from uuid import uuid4

from app.domain.enums import LensType, Role, VetoCategory
from app.domain.methodology import default_methodology
from app.domain.models import Claim, DimensionScore, Scorecard, Veto
from app.modules.rules_engine.service import evaluate


def _strong_sai_scorecards(application_id, n=3) -> list[Scorecard]:
    m = default_methodology()
    cards = []
    for i in range(n):
        cards.append(
            Scorecard(
                application_id=application_id,
                assessor_id=f"assessor-{i}",
                role=Role.TECHNICAL_ASSESSOR,
                lens=LensType.SAI,
                dimension_scores=[DimensionScore(dimension=d, score=8.0) for d in m.sai_weights],
                submitted=True,
            )
        )
    return cards


def test_confirmed_veto_blocks_approval():
    app_id = uuid4()
    result = evaluate(
        scorecards=_strong_sai_scorecards(app_id),
        claims=[Claim(text="c")],
        vetoes=[Veto(category=VetoCategory.ELIGIBILITY, rationale="x", raised_by="u", confirmed=True)],
        methodology=default_methodology(),
        submission_threshold=3,
    )
    reasons = {b.reason for b in result.publication_blocks}
    # A confirmed veto is a hard block on approval states.
    assert "confirmed_veto" in reasons or result.recommended_state.value not in {"fund", "fund_with_conditions"}


def test_incomplete_submissions_block_approval():
    app_id = uuid4()
    result = evaluate(
        scorecards=_strong_sai_scorecards(app_id, n=1),
        claims=[Claim(text="c")],
        vetoes=[],
        methodology=default_methodology(),
        submission_threshold=3,
    )
    if result.recommended_state.value in {"fund", "fund_with_conditions"}:
        assert any(b.reason == "assessment_incomplete" for b in result.publication_blocks)


def test_contradicted_claim_blocks_approval():
    app_id = uuid4()
    result = evaluate(
        scorecards=_strong_sai_scorecards(app_id),
        claims=[Claim(text="c", contradicted=True)],
        vetoes=[],
        methodology=default_methodology(),
        submission_threshold=3,
    )
    if result.recommended_state.value in {"fund", "fund_with_conditions"}:
        assert any(b.reason == "contradicted_evidence" for b in result.publication_blocks)
