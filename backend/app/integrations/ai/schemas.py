"""Structured-output schema for deck claim extraction.

These Pydantic models define the exact shape Claude must return via
``client.messages.parse(output_format=...)``. Constraining the evidence tier to
the governed vocabulary (PRD 6.6) keeps AI proposals inside the same controlled
set an assessor uses — the model proposes a tier; a human still validates it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.enums import EvidenceState


class ExtractedClaim(BaseModel):
    """A single material claim the model found in the deck."""

    text: str = Field(description="The material claim, stated as a single verifiable assertion.")
    slide: int = Field(description="1-indexed slide/page the claim was found on.", ge=1)
    quote: str = Field(description="Short verbatim excerpt from the deck supporting the claim.")
    proposed_evidence_state: EvidenceState = Field(
        description=(
            "Evidence tier this claim warrants BASED ONLY ON THE DECK. A claim "
            "stated in the applicant's own deck with no external proof is "
            "'applicant_declaration_only'. Use 'ai_inference' only if you "
            "inferred it rather than the deck stating it. Do not assume "
            "verification that is not shown."
        )
    )
    rationale: str = Field(description="One sentence on why this tier was assigned.")
    confidence: float = Field(
        description="Your confidence (0-1) that this extraction is accurate.", ge=0, le=1
    )


class DeckExtraction(BaseModel):
    """The full structured result of reviewing one deck."""

    applicant_name: str | None = Field(
        default=None, description="Applicant/company name if stated in the deck."
    )
    sector: str | None = Field(default=None, description="Sector or domain if stated.")
    ask_amount: str | None = Field(
        default=None, description="Funding amount requested, verbatim, if stated."
    )
    claims: list[ExtractedClaim] = Field(
        default_factory=list, description="Material claims extracted from the deck."
    )
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Material claims that lack any supporting evidence and should be requested.",
    )
