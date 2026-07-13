"""Award conditions and milestones (PRD 8.6).

Minimal scaffold: convert decision conditions into milestones. Tranche release
is intentionally a human-authorised action (PRD 12.2) and is left as a Phase 3
deliverable (PRD 21).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.store import store

router = APIRouter(prefix="/awards", tags=["Award Governance"])

# In-memory milestone registry for the scaffold.
_milestones: dict[UUID, dict] = {}


class Milestone(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    application_id: UUID
    description: str
    acceptance_criteria: str
    released: bool = False


@router.post("/applications/{application_id}/milestones", response_model=Milestone, status_code=201)
def create_milestone(application_id: UUID, description: str, acceptance_criteria: str) -> Milestone:
    if application_id not in store.applications:
        raise HTTPException(status_code=404, detail="Application not found")
    milestone = Milestone(
        application_id=application_id,
        description=description,
        acceptance_criteria=acceptance_criteria,
    )
    _milestones[milestone.id] = milestone.model_dump()
    return milestone


@router.get("/applications/{application_id}/milestones", response_model=list[Milestone])
def list_milestones(application_id: UUID) -> list[Milestone]:
    return [Milestone(**m) for m in _milestones.values() if m["application_id"] == application_id]
