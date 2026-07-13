"""Committee decision card and immutable decision record (PRD 8.5)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.store import store
from app.domain.enums import ApplicationStatus, DecisionState
from app.domain.models import DecisionRecord
from app.modules.rules_engine.service import EvaluationResult, evaluate

router = APIRouter(prefix="/committee", tags=["Committee Room"])


@router.get("/applications/{application_id}/decision-card", response_model=EvaluationResult)
def decision_card(
    application_id: UUID,
    submission_threshold: int = Query(default=3, ge=1),
) -> EvaluationResult:
    """One standard decision card per applicant (acceptance criterion 9).

    Surfaces SAI, SSAI, SSEI, EVI, vetoes, the recommended state and any
    publication blocks — a structured card, not a document dump (PRD 8.5).
    """

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    programme = store.programmes.get(app.programme_id)
    methodology = store.methodologies.get(programme.methodology_version if programme else "v0.2")
    if methodology is None:
        raise HTTPException(status_code=409, detail="Methodology not found")
    return evaluate(
        scorecards=store.scorecards_for(application_id),
        claims=store.claims_for(application_id),
        vetoes=store.vetoes_for(application_id),
        methodology=methodology,
        submission_threshold=submission_threshold,
        open_divergence=list(store.divergence_alerts.values()),
    )


class DecisionCreate(BaseModel):
    state: DecisionState
    rationale: str
    decided_by: str
    conditions: list[str] = Field(default_factory=list)
    overridden: bool = False
    override_owner: str | None = None


# Approval states that the publication block can veto (PRD 13).
APPROVAL_STATES = {DecisionState.FUND, DecisionState.FUND_WITH_CONDITIONS}


@router.post("/applications/{application_id}/decision", response_model=DecisionRecord, status_code=201)
def record_decision(
    application_id: UUID,
    payload: DecisionCreate,
    submission_threshold: int = Query(default=3, ge=1),
) -> DecisionRecord:
    """Record an immutable committee decision (PRD 8.5, acceptance #10, #11).

    Enforces the publication block: an approval cannot be recorded while blocks
    remain, unless a named owner supplies an override rationale.
    """

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    programme = store.programmes.get(app.programme_id)
    methodology = store.methodologies.get(programme.methodology_version if programme else "v0.2")
    if methodology is None:
        raise HTTPException(status_code=409, detail="Methodology not found")

    result = evaluate(
        scorecards=store.scorecards_for(application_id),
        claims=store.claims_for(application_id),
        vetoes=store.vetoes_for(application_id),
        methodology=methodology,
        submission_threshold=submission_threshold,
        open_divergence=list(store.divergence_alerts.values()),
    )

    if payload.state in APPROVAL_STATES and result.publication_blocks:
        # Confirmed vetoes can never be overridden (PRD 12.2).
        if result.confirmed_vetoes:
            raise HTTPException(
                status_code=409,
                detail="Approval blocked by confirmed veto and cannot be overridden.",
            )
        if not (payload.overridden and payload.override_owner):
            reasons = [b.reason for b in result.publication_blocks]
            raise HTTPException(
                status_code=409,
                detail={"error": "Approval blocked", "blocks": reasons},
            )

    record = DecisionRecord(
        application_id=application_id,
        state=payload.state,
        rationale=payload.rationale,
        decided_by=payload.decided_by,
        methodology_version=methodology.version,
        framework_versions=[m.framework_version for m in app.mappings],
        conditions=payload.conditions,
        overridden=payload.overridden,
        override_owner=payload.override_owner,
        decided_at=datetime.now(timezone.utc),
    )
    store.decisions[record.id] = record
    app.status = ApplicationStatus.DECIDED
    return record
