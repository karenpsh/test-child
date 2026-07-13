"""Core domain models for SAGE.

These are Pydantic models describing the shape of the governed decision record.
They are storage-agnostic (no ORM yet) so the scaffold can evolve toward a
database without rewriting the domain. Every model that participates in a
decision carries enough lineage to satisfy the Final Product Test (PRD 22):
what was claimed, what evidence existed, how each assessor judged it, where
they disagreed, and why funding was approved.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import (
    ApplicationStatus,
    DecisionState,
    EvidenceState,
    LensType,
    ResolutionState,
    Role,
    StrategicMaturity,
    VetoCategory,
)


class EvidenceCitation(BaseModel):
    """Page- or cell-level pointer to a source document (acceptance #4)."""

    drive_file_id: str
    version: str | None = None
    locator: str = Field(description="Page, cell or range reference, e.g. 'p.4' or 'Sheet1!B12'.")
    excerpt: str | None = None


class Claim(BaseModel):
    """A material assertion extracted from an application (PRD 8.2)."""

    id: UUID = Field(default_factory=uuid4)
    text: str
    evidence_state: EvidenceState = EvidenceState.APPLICANT_DECLARATION_ONLY
    citations: list[EvidenceCitation] = Field(default_factory=list)
    contradicted: bool = False


class DimensionScore(BaseModel):
    """A single dimension score within a lens, on a 0-10 scale."""

    dimension: str = Field(description="Weight key, e.g. 'technical_delivery_credibility'.")
    score: float = Field(ge=0, le=10)
    citations: list[EvidenceCitation] = Field(default_factory=list)


class Scorecard(BaseModel):
    """An independent assessor's locked scorecard (PRD 8.3).

    ``submitted`` gates the blind-scoring reveal (acceptance #5): panel results
    are only revealed after the submission threshold is met.
    """

    id: UUID = Field(default_factory=uuid4)
    application_id: UUID
    assessor_id: str
    role: Role
    lens: LensType
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    conflict_declared: bool = False
    submitted: bool = False
    submitted_at: datetime | None = None


class Veto(BaseModel):
    """A recorded veto (PRD 10.2). A *confirmed* veto blocks approval states."""

    id: UUID = Field(default_factory=uuid4)
    category: VetoCategory
    rationale: str
    raised_by: str
    confirmed: bool = False


class DivergenceAlert(BaseModel):
    """A material divergence requiring annotation/resolution (PRD 8.4, 10.1)."""

    id: UUID = Field(default_factory=uuid4)
    indicator: str
    magnitude: float
    annotation: str | None = None
    resolution: ResolutionState = ResolutionState.UNRESOLVED


class FrameworkMapping(BaseModel):
    """Mapping from a claim/proposal to a framework KPI (PRD 7)."""

    id: UUID = Field(default_factory=uuid4)
    framework_version: str
    objective: str
    kpi: str
    maturity: StrategicMaturity = StrategicMaturity.THEME_MATCH
    proposed_by: str
    validated: bool = False  # FRA-004: unvalidated until an assessor approves
    rationale: str | None = None


class Programme(BaseModel):
    """A funding programme (PRD 8.1)."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    methodology_version: str
    mandatory_framework_packs: list[str] = Field(default_factory=list)
    optional_framework_packs: list[str] = Field(default_factory=list)
    drive_folder_ids: list[str] = Field(default_factory=list)
    published: bool = False


class Application(BaseModel):
    """An application dossier with an immutable id (PRD 8.2, acceptance #3)."""

    id: UUID = Field(default_factory=uuid4)
    programme_id: UUID
    applicant_name: str
    status: ApplicationStatus = ApplicationStatus.INGESTED
    claims: list[Claim] = Field(default_factory=list)
    mappings: list[FrameworkMapping] = Field(default_factory=list)
    created_at: datetime | None = None


class DecisionRecord(BaseModel):
    """The immutable committee decision record (PRD 8.5, acceptance #10, #11)."""

    id: UUID = Field(default_factory=uuid4)
    application_id: UUID
    state: DecisionState
    rationale: str
    decided_by: str
    methodology_version: str
    framework_versions: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    overridden: bool = False
    override_owner: str | None = None
    decided_at: datetime | None = None
