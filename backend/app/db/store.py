"""In-memory repository for the scaffold.

This is a deliberate placeholder so the API runs end-to-end before a database
is selected (an Open Decision, PRD 20). Swap ``InMemoryStore`` for a real
persistence layer without changing the domain models or module services.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.methodology import MethodologyVersion, default_methodology
from app.domain.models import (
    Application,
    Claim,
    DecisionRecord,
    DivergenceAlert,
    Programme,
    Scorecard,
    Veto,
)


class InMemoryStore:
    def __init__(self) -> None:
        self.programmes: dict[UUID, Programme] = {}
        self.applications: dict[UUID, Application] = {}
        self.scorecards: dict[UUID, Scorecard] = {}
        self.vetoes: dict[UUID, Veto] = {}
        self.divergence_alerts: dict[UUID, DivergenceAlert] = {}
        self.decisions: dict[UUID, DecisionRecord] = {}
        self.methodologies: dict[str, MethodologyVersion] = {}

        seed = default_methodology()
        self.methodologies[seed.version] = seed

    # --- convenience accessors -------------------------------------------
    def scorecards_for(self, application_id: UUID) -> list[Scorecard]:
        return [s for s in self.scorecards.values() if s.application_id == application_id]

    def claims_for(self, application_id: UUID) -> list[Claim]:
        app = self.applications.get(application_id)
        return list(app.claims) if app else []

    def vetoes_for(self, application_id: UUID) -> list[Veto]:
        # Vetoes are stored globally in this scaffold; a real store keys them
        # by application. Returns all for now.
        return list(self.vetoes.values())


# Single process-wide store for the scaffold.
store = InMemoryStore()
