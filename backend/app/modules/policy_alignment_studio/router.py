"""Framework mapping and validation (PRD 7.3).

Implements the FRA-004 rule: applicants may propose mappings, but they remain
unvalidated until an assessor approves them.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.store import store
from app.domain.enums import StrategicMaturity
from app.domain.models import FrameworkMapping

router = APIRouter(prefix="/framework", tags=["Policy Alignment Studio"])

# Initial framework packs available for programmes (PRD 7.2).
INITIAL_FRAMEWORK_PACKS = [
    "sarawak_digital_economy_blueprint_2030",
    "post_covid19_development_strategy_2030",
    "sarawak_2030_sustainability_blueprint",
    "sdec_programme_mandates",
    "un_sdg",
    "issb_themes",
    "gri_iris_plus",
]


@router.get("/packs")
def list_framework_packs() -> list[str]:
    return INITIAL_FRAMEWORK_PACKS


class MappingCreate(BaseModel):
    framework_version: str
    objective: str
    kpi: str
    maturity: StrategicMaturity = StrategicMaturity.THEME_MATCH
    proposed_by: str
    rationale: str | None = None


@router.post("/applications/{application_id}/mappings", response_model=FrameworkMapping, status_code=201)
def propose_mapping(application_id: UUID, payload: MappingCreate) -> FrameworkMapping:
    """Propose a mapping (FRA-004). Starts unvalidated."""

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    mapping = FrameworkMapping(validated=False, **payload.model_dump())
    app.mappings.append(mapping)
    return mapping


@router.post("/applications/{application_id}/mappings/{mapping_id}/validate", response_model=FrameworkMapping)
def validate_mapping(application_id: UUID, mapping_id: UUID) -> FrameworkMapping:
    """Assessor validation of a proposed mapping (FRA-004, FRA-005)."""

    app = store.applications.get(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    for mapping in app.mappings:
        if mapping.id == mapping_id:
            mapping.validated = True
            return mapping
    raise HTTPException(status_code=404, detail="Mapping not found")
