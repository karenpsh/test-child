"""Executive portfolio views (PRD 14.1)."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from app.db.store import store
from app.domain.enums import ApplicationStatus, DecisionState

router = APIRouter(prefix="/portfolio", tags=["Portfolio Intelligence"])


@router.get("/summary")
def portfolio_summary() -> dict:
    """High-level counts across the pipeline (PRD 14.1).

    A scaffold aggregation: applications by status, decisions by state, and
    open governance items (unresolved divergence, confirmed vetoes).
    """

    apps = list(store.applications.values())
    decisions = list(store.decisions.values())

    status_counts = Counter(a.status.value for a in apps)
    decision_counts = Counter(d.state.value for d in decisions)

    confirmed_vetoes = sum(1 for v in store.vetoes.values() if v.confirmed)
    open_divergence = sum(
        1
        for a in store.divergence_alerts.values()
        if a.resolution.value in ("unresolved", "escalated")
    )
    overrides = sum(1 for d in decisions if d.overridden)

    return {
        "applications_total": len(apps),
        "applications_by_status": {s.value: status_counts.get(s.value, 0) for s in ApplicationStatus},
        "decisions_by_state": {s.value: decision_counts.get(s.value, 0) for s in DecisionState},
        "open_governance": {
            "confirmed_vetoes": confirmed_vetoes,
            "open_divergence_alerts": open_divergence,
            "overrides": overrides,
        },
    }
