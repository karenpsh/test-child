"""Aggregate API router wiring every functional module (PRD 11)."""

from __future__ import annotations

from fastapi import APIRouter

from app.integrations.google_drive.router import router as drive_router
from app.modules.assessment_workspace.router import router as assessment_router
from app.modules.audit_service.router import router as audit_router
from app.modules.award_governance.router import router as award_router
from app.modules.committee_room.router import router as committee_router
from app.modules.evidence_vault.router import router as evidence_router
from app.modules.policy_alignment_studio.router import router as policy_router
from app.modules.portfolio_intelligence.router import router as portfolio_router
from app.modules.programme_studio.router import router as programme_router
from app.modules.rules_engine.router import router as rules_router

api_router = APIRouter()

# Order mirrors the core workflow (PRD 8).
api_router.include_router(programme_router)
api_router.include_router(drive_router)
api_router.include_router(evidence_router)
api_router.include_router(policy_router)
api_router.include_router(assessment_router)
api_router.include_router(rules_router)
api_router.include_router(committee_router)
api_router.include_router(award_router)
api_router.include_router(portfolio_router)
api_router.include_router(audit_router)
