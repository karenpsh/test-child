# SAGE — Sarawak Allocation and Grant Evaluation

> A governed decision operating system for funding evidence, strategic alignment,
> sustainability and measurable outcomes.
>
> **Fund evidence. Govern outcomes.**

SAGE evaluates, approves, monitors and learns from innovation grants, startup
funding and strategic investments. It converts applications, pitch decks,
scoring sheets and assessor comments into a **structured, auditable decision
record**. SAGE does not replace SDEC's judgement — it makes that judgement
consistent, evidence-linked, policy-aware, auditable and measurable.

This repository is the **initial scaffold** produced from the SAGE PRD (v0.2).
It stands up the decision-control core end-to-end so subsequent work has a
running foundation rather than a blank page.

## Product doctrine — five independent lenses

| Question | Lens |
| :---- | :---- |
| Does the venture merit funding? | **SAI** · Sarawak Allocation Index |
| Why should Sarawak support it? | **SSAI** · Sarawak Strategic Alignment Index |
| What sustainability value or risk does it create? | **SSEI** · Sarawak Sustainability and ESG Index |
| How much of the story can be trusted? | **EVI** · Evidence Veracity Index |
| What non-negotiable risks apply? | Risk and Veto Profile |

The lenses are computed **independently and never blended** (PRD §6). Generative
AI never scores, sets eligibility, raises vetoes or releases funds (PRD §10, §12).

## Repository layout

```
.
├── backend/            FastAPI service — the governed decision engine
│   └── app/
│       ├── domain/         Enums, versioned methodology, domain models
│       ├── modules/        The nine functional modules (PRD §11)
│       │   ├── programme_studio/
│       │   ├── evidence_vault/
│       │   ├── policy_alignment_studio/
│       │   ├── assessment_workspace/
│       │   ├── rules_engine/       ← SAI/SSAI/SSEI/EVI, divergence, veto, blocks
│       │   ├── committee_room/
│       │   ├── award_governance/
│       │   ├── portfolio_intelligence/
│       │   └── audit_service/
│       └── integrations/google_drive/   Drive folder auth + file index (PRD §9)
├── frontend/           React + TypeScript UI — decision card and portfolio views
└── docs/               PRD-to-code traceability
```

The backend maps **one package per functional module** in PRD §11. The Rules
Engine (`app/modules/rules_engine`) is the product's core doctrine and is
implemented with real, deterministic, unit-tested logic.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000/docs
pytest                             # 15 tests: indices, matrix, publication blocks
```

### Frontend

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173  (proxies /api to :8000)
```

## What works today

Run the backend, open `/docs`, and you can drive the full governed workflow:

1. **Programme Studio** — create a programme, assign framework packs, publish
   (publish requires an SDEC-approved methodology version).
2. **Evidence Vault** — ingest an application (immutable id), register claims
   with page/cell-level evidence lineage.
3. **Assessment Workspace** — submit blind, independent scorecards; the panel
   view stays hidden until the submission threshold is met.
4. **Rules Engine** — reproducible SAI/SSAI/SSEI/EVI, divergence detection,
   veto handling, and publication blocks.
5. **Committee Room** — a single structured decision card; recording an approval
   is refused while publication blocks remain (confirmed vetoes cannot be
   overridden).
6. **Portfolio Intelligence** — pipeline and open-governance summary.
7. **Audit Service** — full immutable-lineage export for any application.

See [`docs/PRD_TRACEABILITY.md`](docs/PRD_TRACEABILITY.md) for how the code maps
to PRD requirements and the twelve MVP acceptance criteria (§17).

## Deliberate scaffold boundaries

- **Persistence** is an in-memory store (`app/db/store.py`) — swap for a database
  without touching the domain models. (Drive-as-system-of-record is an open
  decision, PRD §20.)
- **Google Drive** exposes the folder-authorisation and file-index surface;
  live OAuth wiring is deferred pending PRD §20 decisions.
- **Auth / tenancy** (PRD §13) is not yet wired.
- **Award milestone disbursement** is a stub — Roadmap Phase 3 (PRD §21).

## Non-functional targets (PRD §15)

99.5% monthly availability · standard screens < 3s, dashboards < 5s ·
10,000 applications/tenant/year · WCAG 2.1 AA target · automated backups.
