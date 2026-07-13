"""Audit export (PRD 13, acceptance criterion 12).

Reconstructs an application's full lineage — claims, scorecards, divergence,
vetoes and the decision record — into a single export package. In production
this reads an append-only event log; the scaffold assembles from the store.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db.store import store

router = APIRouter(prefix="/audit", tags=["Audit Service"])


@router.get("/applications/{application_id}/export")
def export_audit_package(application_id: UUID) -> dict:
    """Immutable-lineage export for one application (acceptance criterion 12)."""

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")

    programme = store.programmes.get(app.programme_id)
    decisions = [d for d in store.decisions.values() if d.application_id == application_id]

    return {
        "application": app.model_dump(mode="json"),
        "programme": programme.model_dump(mode="json") if programme else None,
        "methodology_version": programme.methodology_version if programme else None,
        "scorecards": [s.model_dump(mode="json") for s in store.scorecards_for(application_id)],
        "vetoes": [v.model_dump(mode="json") for v in store.vetoes_for(application_id)],
        "divergence_alerts": [a.model_dump(mode="json") for a in store.divergence_alerts.values()],
        "decisions": [d.model_dump(mode="json") for d in decisions],
    }
