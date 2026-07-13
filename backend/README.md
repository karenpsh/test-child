# SAGE Backend

FastAPI service implementing the SAGE governed decision engine. One package per
functional module (PRD §11); the Rules Engine holds the deterministic core.

## Run

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000/docs
pytest                            # 15 tests
```

## Layout

- `app/domain/` — `enums.py` (controlled vocabularies), `methodology.py`
  (versioned weights/thresholds), `models.py` (decision-record shapes).
- `app/modules/<module>/` — `router.py` (+ `service.py` where logic warrants).
- `app/modules/rules_engine/` — `indices.py`, `divergence.py`,
  `decision_matrix.py`, `service.py` (composition + publication blocks).
- `app/integrations/google_drive/` — folder auth + file index (PRD §9).
- `app/db/store.py` — in-memory store (swap for a real DB).

## Key invariants

- Indices are pure and reproducible from stored inputs (acceptance #6).
- No generative AI touches scores, eligibility, vetoes or decisions (PRD §10, §12.2).
- Approval states are blocked while assessments are incomplete, material
  divergence is unresolved, evidence is contradicted, or a veto is confirmed
  (PRD §13). Confirmed vetoes cannot be overridden.
- Methodology is versioned; historical decisions retain their version (acceptance #11).
