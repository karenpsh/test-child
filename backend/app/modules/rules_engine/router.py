"""HTTP surface for the Rules Engine."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.db.store import store
from app.modules.rules_engine.service import EvaluationResult, evaluate

router = APIRouter(prefix="/rules-engine", tags=["Rules Engine"])


@router.get("/applications/{application_id}/evaluation", response_model=EvaluationResult)
def get_evaluation(
    application_id: UUID,
    submission_threshold: int = Query(default=3, ge=1, description="Required submitted scorecards."),
) -> EvaluationResult:
    """Reproducible evaluation for an application (acceptance criteria 6, 7, 8)."""

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")

    programme = store.programmes.get(app.programme_id)
    methodology_version = programme.methodology_version if programme else "v0.2"
    methodology = store.methodologies.get(methodology_version)
    if methodology is None:
        raise HTTPException(status_code=409, detail=f"Methodology {methodology_version} not found")

    return evaluate(
        scorecards=store.scorecards_for(application_id),
        claims=store.claims_for(application_id),
        vetoes=store.vetoes_for(application_id),
        methodology=methodology,
        submission_threshold=submission_threshold,
        open_divergence=list(store.divergence_alerts.values()),
    )
