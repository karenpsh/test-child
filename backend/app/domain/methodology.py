"""Versioned methodology objects consumed by the Rules Engine.

A ``MethodologyVersion`` bundles the weights, confidence tiers and thresholds
that were in force when a decision was made. Historical decisions store the
methodology version id (acceptance criterion 11), so re-running the Rules
Engine over stored inputs reproduces the original indices (acceptance
criterion 6).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.core import config
from app.domain.enums import EvidenceState


class MethodologyVersion(BaseModel):
    """Immutable snapshot of scoring configuration.

    Instances should be treated as read-only once referenced by a decision.
    ``require_approval`` reflects PRD 6.1: weights need SDEC methodology
    approval before production use.
    """

    version: str = Field(description="Methodology version identifier, e.g. 'v0.2'.")
    approved: bool = Field(
        default=False,
        description="Whether SDEC has approved this methodology for production.",
    )

    sai_weights: dict[str, float]
    ssai_weights: dict[str, float]
    ssei_weights: dict[str, float]
    evidence_confidence: dict[EvidenceState, float]

    individual_outlier_threshold: float = 3.0

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> "MethodologyVersion":
        for name, weights in (
            ("sai_weights", self.sai_weights),
            ("ssai_weights", self.ssai_weights),
            ("ssei_weights", self.ssei_weights),
        ):
            total = sum(weights.values())
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"{name} must sum to 1.0, got {total:.6f}")
        return self


# Default evidence confidence weights (PRD 6.6).
EVIDENCE_CONFIDENCE_V0_2: dict[EvidenceState, float] = {
    EvidenceState.INDEPENDENTLY_VERIFIED: 1.00,
    EvidenceState.CONTRACTUAL_OR_SYSTEM_GENERATED: 0.90,
    EvidenceState.THIRD_PARTY_DOCUMENTED: 0.80,
    EvidenceState.APPLICANT_DATA_WITH_SUPPORT: 0.60,
    EvidenceState.APPLICANT_DECLARATION_ONLY: 0.30,
    EvidenceState.AI_INFERENCE: 0.10,
    EvidenceState.CONTRADICTED: 0.00,
}


def default_methodology() -> MethodologyVersion:
    """The seed methodology bundled with SAGE (PRD v0.2 defaults)."""

    return MethodologyVersion(
        version=config.settings.default_methodology_version,
        approved=False,  # requires explicit SDEC approval before production use
        sai_weights=dict(config.SAI_WEIGHTS_V0_2),
        ssai_weights=dict(config.SSAI_WEIGHTS_V0_2),
        ssei_weights=dict(config.SSEI_WEIGHTS_V0_2),
        evidence_confidence=dict(EVIDENCE_CONFIDENCE_V0_2),
        individual_outlier_threshold=config.settings.individual_outlier_threshold,
    )
