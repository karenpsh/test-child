# SAGE Frontend

React + TypeScript (Vite) UI for SAGE. Two views today:

- **Decision Card** (`src/pages/DecisionCard.tsx`) — one structured committee
  card per applicant: the four lenses (SAI/SSAI/SSEI/EVI), the recommended
  state, confirmed vetoes, publication blocks and divergence alerts (PRD §8.5).
- **Portfolio** (`src/pages/PortfolioDashboard.tsx`) — pipeline counts and open
  governance items (PRD §14.1).

## Run

```bash
npm install
npm run dev        # http://localhost:5173, proxies /api → http://localhost:8000
npm run build      # type-check (strict) + production build
```

Start the backend first (`uvicorn app.main:app --reload` in `../backend`). The
Vite dev server proxies `/api` to it. API types in `src/types.ts` mirror the
Rules Engine output.
