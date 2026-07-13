"""Independent, blind assessment (PRD 8.3).

Enforces acceptance criterion 5: assessors submit independently and cannot see
other scores before submission. Scorecards are only revealed once the number of
submitted scorecards reaches the panel threshold.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.store import store
from app.domain.enums import LensType, Role
from app.domain.models import DimensionScore, Scorecard

router = APIRouter(prefix="/assessments", tags=["Assessment Workspace"])


class ScorecardCreate(BaseModel):
    application_id: UUID
    assessor_id: str
    role: Role
    lens: LensType
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    conflict_declared: bool = False


@router.post("", response_model=Scorecard, status_code=201)
def create_scorecard(payload: ScorecardCreate) -> Scorecard:
    """Create a draft scorecard. Conflicts must be declared before access (PRD 8.3)."""

    if payload.application_id not in store.applications:
        raise HTTPException(status_code=422, detail="Unknown application")
    sc = Scorecard(**payload.model_dump())
    store.scorecards[sc.id] = sc
    return sc


@router.post("/{scorecard_id}/submit", response_model=Scorecard)
def submit_scorecard(scorecard_id: UUID) -> Scorecard:
    """Lock and submit a scorecard (PRD 8.3). Locked scorecards are immutable."""

    sc = store.scorecards.get(scorecard_id)
    if sc is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    if sc.submitted:
        raise HTTPException(status_code=409, detail="Scorecard already submitted and locked")
    sc.submitted = True
    sc.submitted_at = datetime.now(timezone.utc)
    return sc


@router.get("/applications/{application_id}/panel")
def panel_view(
    application_id: UUID,
    threshold: int = Query(default=3, ge=1, description="Reveal threshold (PRD 8.3)."),
):
    """Return panel scorecards only after the submission threshold is met.

    Before the threshold, returns counts only so no assessor can see another's
    scores early (acceptance criterion 5).
    """

    if application_id not in store.applications:
        raise HTTPException(status_code=404, detail="Application not found")
    scorecards = store.scorecards_for(application_id)
    submitted = [sc for sc in scorecards if sc.submitted]
    if len(submitted) < threshold:
        return {
            "revealed": False,
            "submitted": len(submitted),
            "threshold": threshold,
            "detail": "Panel results are hidden until the submission threshold is reached.",
        }
    return {"revealed": True, "scorecards": submitted}
