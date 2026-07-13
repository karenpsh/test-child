"""Programme creation and configuration (PRD 8.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.store import store
from app.domain.models import Programme

router = APIRouter(prefix="/programmes", tags=["Programme Studio"])


class ProgrammeCreate(BaseModel):
    name: str
    methodology_version: str = "v0.2"
    mandatory_framework_packs: list[str] = Field(default_factory=list)
    optional_framework_packs: list[str] = Field(default_factory=list)
    drive_folder_ids: list[str] = Field(default_factory=list)


@router.post("", response_model=Programme, status_code=201)
def create_programme(payload: ProgrammeCreate) -> Programme:
    if payload.methodology_version not in store.methodologies:
        raise HTTPException(status_code=422, detail="Unknown methodology version")
    programme = Programme(**payload.model_dump())
    store.programmes[programme.id] = programme
    return programme


@router.get("", response_model=list[Programme])
def list_programmes() -> list[Programme]:
    return list(store.programmes.values())


@router.get("/{programme_id}", response_model=Programme)
def get_programme(programme_id: UUID) -> Programme:
    programme = store.programmes.get(programme_id)
    if programme is None:
        raise HTTPException(status_code=404, detail="Programme not found")
    return programme


@router.post("/{programme_id}/publish", response_model=Programme)
def publish_programme(programme_id: UUID) -> Programme:
    """Publish the funding call (PRD 8.1). Requires an approved methodology."""

    programme = store.programmes.get(programme_id)
    if programme is None:
        raise HTTPException(status_code=404, detail="Programme not found")
    methodology = store.methodologies.get(programme.methodology_version)
    if methodology is None or not methodology.approved:
        raise HTTPException(
            status_code=409,
            detail="Methodology must be SDEC-approved before publishing (PRD 6.1).",
        )
    programme.published = True
    return programme
