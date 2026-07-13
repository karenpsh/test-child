"""Application ingestion, claim registry and evidence lineage (PRD 8.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.db.store import store
from app.domain.enums import EvidenceState, VerificationStatus
from app.domain.methodology import default_methodology
from app.domain.models import Application, Claim, EvidenceCitation
from app.integrations.ai.deck_extraction import Contradiction, review_deck
from app.modules.rules_engine.indices import compute_evi

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


class DeckReviewResponse(BaseModel):
    """Result of an AI deck review (PRD 8.2, 12). A structured, auditable
    proposal — every claim is unverified until a human accepts it."""

    model_version: str
    live: bool
    claims: list[Claim]
    evidence_gaps: list[str]
    evi_preview: float = Field(description="EVI over non-rejected claims, 0-10 scale.")


@router.post("/applications/{application_id}/deck:extract", response_model=DeckReviewResponse)
async def extract_deck(
    application_id: UUID,
    file: UploadFile = File(..., description="Applicant pitch deck (PDF)."),
    deck_file_id: str = Form(default="uploaded-deck"),
) -> DeckReviewResponse:
    """Run AI extraction over an uploaded deck (PRD 12.1).

    Produces *proposed, unvalidated* claims with slide-level citations,
    confidence and model version (PRD 12.3). Uses Claude when a key is set,
    otherwise a deterministic offline extractor. Contradictions are flagged
    against the application's already-verified claims.
    """

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")

    pdf_bytes = await file.read()

    # Contradiction sources: existing verified/contractual claims act as facts.
    contradictions = [
        Contradiction(keyword=w, note=f"Conflicts with verified claim: {c.text}")
        for c in app.claims
        if c.verification_status == VerificationStatus.ACCEPTED and not c.ai_generated
        for w in [c.text.split()[0]]
        if w
    ]

    result = review_deck(pdf_bytes, deck_file_id=deck_file_id, known_contradictions=contradictions)
    app.claims.extend(result.claims)

    non_rejected = [
        c for c in result.claims if c.verification_status != VerificationStatus.REJECTED
    ]
    evi = compute_evi(non_rejected, default_methodology()).value

    return DeckReviewResponse(
        model_version=result.model_version,
        live=result.live,
        claims=result.claims,
        evidence_gaps=result.extraction.evidence_gaps,
        evi_preview=evi,
    )


class ClaimVerify(BaseModel):
    decision: VerificationStatus = Field(description="accepted | edited | rejected")
    edited_text: str | None = None
    edited_evidence_state: EvidenceState | None = None


@router.post("/applications/{application_id}/claims/{claim_id}/verify", response_model=Claim)
def verify_claim(application_id: UUID, claim_id: UUID, payload: ClaimVerify) -> Claim:
    """Human accept / edit / reject of an AI-proposed claim (PRD 12.3).

    The original AI text is preserved in ``ai_original_text`` so the correction
    stays auditable, regardless of the edit.
    """

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    claim = next((c for c in app.claims if c.id == claim_id), None)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if payload.decision == VerificationStatus.EDITED:
        if payload.edited_text is not None:
            claim.text = payload.edited_text
        if payload.edited_evidence_state is not None:
            claim.evidence_state = payload.edited_evidence_state
    claim.verification_status = payload.decision
    return claim
