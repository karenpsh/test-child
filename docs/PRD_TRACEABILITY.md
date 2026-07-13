# PRD → Code Traceability

Maps SAGE PRD v0.2 sections to the scaffold implementation. Legend:
✅ implemented · 🟡 partial / surface only · ⬜ deferred (documented boundary).

## Functional modules (PRD §11)

| Module | Package | Status |
| :---- | :---- | :---- |
| Programme Studio | `app/modules/programme_studio` | ✅ create, list, publish (methodology-gated) |
| Evidence Vault | `app/modules/evidence_vault` | ✅ ingest, claims, evidence citations, AI deck extraction + human verify (accept/edit/reject) |
| Policy Alignment Studio | `app/modules/policy_alignment_studio` | ✅ packs, propose/validate mappings (FRA-004) · 🟡 framework decomposition |
| Assessment Workspace | `app/modules/assessment_workspace` | ✅ blind scorecards, threshold reveal, lock |
| Rules Engine | `app/modules/rules_engine` | ✅ SAI/SSAI/SSEI/EVI, decision matrix, divergence, vetoes, publication blocks |
| Committee Room | `app/modules/committee_room` | ✅ decision card, immutable decision, override rules |
| Award Governance | `app/modules/award_governance` | 🟡 milestones stub · ⬜ tranche release (Phase 3) |
| Portfolio Intelligence | `app/modules/portfolio_intelligence` | 🟡 pipeline + governance summary |
| Audit Service | `app/modules/audit_service` | ✅ full lineage export · 🟡 append-only event log |

## Multi-lens architecture (PRD §6)

| PRD | Implementation |
| :---- | :---- |
| §6.1 SAI weights | `core/config.py::SAI_WEIGHTS_V0_2`, `rules_engine/indices.py::compute_sai` |
| §6.2 SSAI weights | `SSAI_WEIGHTS_V0_2`, `compute_ssai` |
| §6.4 SSEI components | `SSEI_WEIGHTS_V0_2`, `compute_ssei` |
| §6.6 EVI confidence tiers | `domain/methodology.py::EVIDENCE_CONFIDENCE_V0_2`, `compute_evi` |
| §6.7 Decision matrix | `rules_engine/decision_matrix.py::recommend` |
| §6.3 Strategic maturity | `domain/enums.py::StrategicMaturity` |

Confidence weights are **not** blended into SAI/SSAI/SSEI (PRD §6.6) — EVI is
returned as a separate lens.

## Decision Control Engine (PRD §10)

| PRD | Implementation |
| :---- | :---- |
| §10.1 Divergence indicators | `rules_engine/divergence.py` |
| §10.2 Veto categories | `domain/enums.py::VetoCategory`, enforced in `service.py` / committee router |
| §10.3 Decision taxonomy | `domain/enums.py::DecisionState` |
| Determinism / no AI in scoring | Pure functions; no model calls anywhere in `rules_engine` |

## AI Requirements (PRD §12)

| PRD | Implementation |
| :---- | :---- |
| §12.1 Permitted — document extraction, claim & contradiction detection, evidence-gap suggestion | `app/integrations/ai/deck_extraction.py::review_deck` (Claude `messages.parse` + deterministic fallback) |
| §12.2 Prohibited — AI never scores, sets eligibility, vetoes or decides | Rules Engine is pure and AI-free; extraction only proposes claims |
| §12.3 Output controls — source, confidence, model version, verification status; accept/edit/reject; original + correction auditable | `Claim.ai_*` fields + `VerificationStatus`; `evidence_vault::verify_claim` preserves `ai_original_text` |

Endpoints: `POST /applications/{id}/deck:extract`, `POST /applications/{id}/claims/{id}/verify`.
Live path requires `ANTHROPIC_API_KEY` (`claude-opus-4-8`); otherwise a deterministic offline extractor runs so the pipeline is testable without credentials.

## Google Drive (PRD §9)

`app/integrations/google_drive/router.py` — DRV-001 scopes, DRV-002 folder
authorisation, DRV-004 file index (id/version/checksum/owner/association).
Live OAuth + change-watch deferred pending PRD §20 (#7).

## MVP acceptance criteria (PRD §17)

| # | Criterion | Where |
| :---- | :---- | :---- |
| 1 | Configure one programme + framework packs | `programme_studio` |
| 2 | Connect only to authorised Drive folders | `google_drive/router.py` |
| 3 | Immutable id + visible status | `domain/models.py::Application`, `evidence_vault` |
| 4 | Page/cell-level evidence lineage | `domain/models.py::EvidenceCitation` |
| 5 | Blind independent submission | `assessment_workspace::panel_view` |
| 6 | Reproducible SAI/SSAI/SSEI/EVI | `rules_engine/indices.py` + `tests/test_indices.py` |
| 7 | Divergence alert blocks finalisation | `rules_engine/service.py::_publication_blocks` |
| 8 | Confirmed veto blocks approval | `committee_room/router.py::record_decision` |
| 9 | One standard decision card | `committee_room::decision_card` |
| 10 | Overrides need owner + rationale + timestamp | `DecisionRecord`, override gate |
| 11 | Historical methodology/framework versions | `DecisionRecord.methodology_version`, `framework_versions` |
| 12 | Complete audit export | `audit_service::export_audit_package` |

## Tests

`backend/tests/` — `test_indices.py`, `test_decision_matrix.py`,
`test_publication_block.py` (15 tests). Run with `pytest` from `backend/`.

## Deferred (documented boundaries)

Persistence layer, live Drive OAuth, auth/tenancy (§13), AI extraction pipeline
(§12.1), milestone disbursement (§8.6 / Phase 3), predictive analytics (§14.2).
