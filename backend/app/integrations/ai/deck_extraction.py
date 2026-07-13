"""Pitch-deck review pipeline (PRD 8.2, 12.1).

Turns an uploaded deck (PDF) into a registry of *proposed, unvalidated* claims,
each with a slide-level citation, a proposed evidence tier and an extraction
confidence. Contradictions are flagged against other indexed evidence. Nothing
here scores or decides — it produces evidence for a human assessor to verify
(PRD 12.2, 12.3).

Two execution paths:

* **Live** — when ``ANTHROPIC_API_KEY`` is configured, Claude reads the deck via
  the Messages API structured-output path (``claude-opus-4-8``) and returns a
  validated :class:`DeckExtraction`.
* **Fallback** — a deterministic, offline heuristic extractor so the pipeline is
  runnable and testable without credentials. It is clearly labelled as such
  (``model_version = "heuristic-fallback"``) and is *not* a substitute for the
  model in production.
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass, field

from app.domain.enums import EvidenceState, VerificationStatus
from app.domain.models import Claim, EvidenceCitation
from app.integrations.ai.schemas import DeckExtraction, ExtractedClaim

MODEL = "claude-opus-4-8"

_EXTRACTION_SYSTEM = (
    "You are an evidence-extraction assistant for a governed grant-evaluation "
    "system. Extract material, verifiable claims from the applicant's pitch "
    "deck. You do NOT score, judge, approve or reject — you only surface "
    "evidence for a human assessor. For each claim assign the evidence tier it "
    "warrants based ONLY on what the deck shows; a claim asserted in the "
    "applicant's own deck with no external proof is 'applicant_declaration_only'. "
    "Never assume verification that is not present."
)


@dataclass
class Contradiction:
    """A known fact that contradicts applicant claims mentioning ``keyword``."""

    keyword: str
    note: str


@dataclass
class DeckReviewResult:
    """Output of a deck review, before human validation."""

    extraction: DeckExtraction
    model_version: str
    live: bool
    claims: list[Claim] = field(default_factory=list)


def review_deck(
    pdf_bytes: bytes,
    *,
    deck_file_id: str,
    known_contradictions: list[Contradiction] | None = None,
) -> DeckReviewResult:
    """Extract claims from a deck and flag contradictions."""

    live = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if live:
        extraction, model_version = _extract_live(pdf_bytes)
    else:
        extraction, model_version = _extract_fallback(pdf_bytes)

    claims = [
        _to_domain_claim(c, deck_file_id, model_version, known_contradictions or [])
        for c in extraction.claims
    ]
    return DeckReviewResult(
        extraction=extraction, model_version=model_version, live=live, claims=claims
    )


# --- Live path -------------------------------------------------------------
def _extract_live(pdf_bytes: bytes) -> tuple[DeckExtraction, str]:
    """Call Claude with the deck as a PDF document block and a structured schema.

    Uses ``messages.parse`` so the response is validated against
    :class:`DeckExtraction`. Citations are captured as a schema field (the
    citations *feature* is incompatible with structured outputs).
    """

    import anthropic

    client = anthropic.Anthropic(max_retries=2)
    b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    response = client.messages.parse(
        model=MODEL,
        max_tokens=8000,
        system=_EXTRACTION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract every material claim from this pitch deck. "
                            "Record the slide number and a short verbatim quote "
                            "for each, and list any claims that lack supporting "
                            "evidence."
                        ),
                    },
                ],
            }
        ],
        output_format=DeckExtraction,
    )
    parsed = response.parsed_output
    if parsed is None:  # refusal or parse failure — degrade rather than crash
        return DeckExtraction(), f"{MODEL} (no parse)"
    return parsed, MODEL


# --- Fallback path ---------------------------------------------------------
_SALIENT = re.compile(
    r"(RM\s?[\d,.]+|[$€£]\s?[\d,.]+|\b\d[\d,.]*\s?%|\bARR\b|\brevenue\b|\bjobs?\b|"
    r"\bcustomers?\b|\busers?\b|\bLOI\b|\bpilot\b|\bcontract\b|\bpatent\b)",
    re.IGNORECASE,
)


def _extract_fallback(pdf_bytes: bytes) -> tuple[DeckExtraction, str]:
    """Deterministic offline extractor. Salient lines become declaration-tier
    claims. Clearly labelled; not a production substitute for the model."""

    pages = _pdf_pages(pdf_bytes)
    claims: list[ExtractedClaim] = []
    gaps: list[str] = []
    applicant = pages[0].splitlines()[0].strip() if pages and pages[0].strip() else None

    for idx, page_text in enumerate(pages, start=1):
        for line in page_text.splitlines():
            line = line.strip()
            if len(line) < 8 or not _SALIENT.search(line):
                continue
            claims.append(
                ExtractedClaim(
                    text=line,
                    slide=idx,
                    quote=line[:120],
                    proposed_evidence_state=EvidenceState.APPLICANT_DECLARATION_ONLY,
                    rationale="Stated in the applicant's own deck without external proof.",
                    confidence=0.5,
                )
            )
            if not re.search(r"(signed|audited|verified|contract|certificate)", line, re.I):
                gaps.append(line[:80])

    return (
        DeckExtraction(applicant_name=applicant, claims=claims, evidence_gaps=gaps[:10]),
        "heuristic-fallback",
    )


def _pdf_pages(pdf_bytes: bytes) -> list[str]:
    try:
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(pdf_bytes))
        return [(page.extract_text() or "") for page in reader.pages]
    except Exception:
        # Not a parseable PDF (e.g. plain text in tests) — treat as one page.
        return [pdf_bytes.decode("utf-8", errors="ignore")]


# --- Mapping ---------------------------------------------------------------
def _to_domain_claim(
    extracted: ExtractedClaim,
    deck_file_id: str,
    model_version: str,
    contradictions: list[Contradiction],
) -> Claim:
    contradicted = False
    note: str | None = None
    for c in contradictions:
        if c.keyword.lower() in extracted.text.lower():
            contradicted = True
            note = c.note
            break

    evidence_state = (
        EvidenceState.CONTRADICTED if contradicted else extracted.proposed_evidence_state
    )
    return Claim(
        text=extracted.text,
        evidence_state=evidence_state,
        citations=[
            EvidenceCitation(
                drive_file_id=deck_file_id,
                locator=f"slide {extracted.slide}",
                excerpt=extracted.quote,
            )
        ],
        contradicted=contradicted,
        contradiction_note=note,
        ai_generated=True,
        ai_model_version=model_version,
        ai_confidence=extracted.confidence,
        ai_original_text=extracted.text,
        verification_status=VerificationStatus.UNVERIFIED,
    )
