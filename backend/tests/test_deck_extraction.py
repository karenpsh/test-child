"""Tests for the AI deck-extraction pipeline (PRD 12).

These exercise the deterministic fallback path (no ANTHROPIC_API_KEY), which is
the path CI runs. The live Claude path shares the same mapping and contradiction
logic, so these tests cover the governed behaviour that matters: proposed claims
are unverified, carry provenance, and contradictions tank a claim's tier.
"""

from __future__ import annotations

from pathlib import Path

from app.domain.enums import EvidenceState, VerificationStatus
from app.integrations.ai.deck_extraction import Contradiction, review_deck

DECK = Path(__file__).parent / "fixtures" / "sample_deck.pdf"


def _deck_bytes() -> bytes:
    return DECK.read_bytes()


def test_extracts_claims_with_provenance():
    result = review_deck(_deck_bytes(), deck_file_id="deck-1")
    assert result.claims, "expected at least one extracted claim"
    for claim in result.claims:
        # PRD 12.3 output controls present on every AI output.
        assert claim.ai_generated is True
        assert claim.ai_model_version
        assert claim.ai_confidence is not None
        assert claim.verification_status is VerificationStatus.UNVERIFIED
        # Page-level lineage (acceptance criterion 4).
        assert claim.citations and claim.citations[0].locator.startswith("slide ")


def test_deck_claims_default_to_declaration_tier():
    result = review_deck(_deck_bytes(), deck_file_id="deck-1")
    # A claim in the applicant's own deck is a declaration, not verified.
    assert any(
        c.evidence_state is EvidenceState.APPLICANT_DECLARATION_ONLY for c in result.claims
    )


def test_contradiction_flags_claim_and_sets_zero_tier():
    result = review_deck(
        _deck_bytes(),
        deck_file_id="deck-1",
        known_contradictions=[
            Contradiction(keyword="ARR", note="Bank records show RM 0.9M ARR, not RM 4.2M")
        ],
    )
    contradicted = [c for c in result.claims if c.contradicted]
    assert contradicted, "expected the ARR claim to be flagged"
    for c in contradicted:
        assert c.evidence_state is EvidenceState.CONTRADICTED
        assert c.contradiction_note


def test_fallback_used_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = review_deck(_deck_bytes(), deck_file_id="deck-1")
    assert result.live is False
    assert result.model_version == "heuristic-fallback"
