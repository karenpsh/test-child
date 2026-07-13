"""Application ingestion, claim registry and evidence lineage (PRD 8.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.store import store
from app.domain.enums import EvidenceState
from app.domain.models import Application, Claim, EvidenceCitation

router = APIRouter(tags=["Evidence Vault"])


class ApplicationCreate(BaseModel):
    programme_id: UUID
    applicant_name: str


@router.post("/applications", response_model=Application, status_code=201)
def ingest_application(payload: ApplicationCreate) -> Application:
    """Generate an immutable application id and visible status (acceptance #3)."""

    if payload.programme_id not in store.programmes:
        raise HTTPException(status_code=422, detail="Unknown programme")
    app = Application(
        programme_id=payload.programme_id,
        applicant_name=payload.applicant_name,
        created_at=datetime.now(timezone.utc),
    )
    store.applications[app.id] = app
    return app


@router.get("/applications", response_model=list[Application])
def list_applications() -> list[Application]:
    return list(store.applications.values())


@router.get("/applications/{application_id}", response_model=Application)
def get_application(application_id: UUID) -> Application:
    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


class ClaimCreate(BaseModel):
    text: str
    evidence_state: EvidenceState = EvidenceState.APPLICANT_DECLARATION_ONLY
    citations: list[EvidenceCitation] = Field(default_factory=list)
    contradicted: bool = False


@router.post("/applications/{application_id}/claims", response_model=Claim, status_code=201)
def add_claim(application_id: UUID, payload: ClaimCreate) -> Claim:
    """Register a material claim with page/cell-level lineage (acceptance #4)."""

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    claim = Claim(**payload.model_dump())
    app.claims.append(claim)
    return claim
