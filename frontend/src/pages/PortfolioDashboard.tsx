import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { PortfolioSummary } from "../types";

// Executive portfolio view (PRD 14.1).
export function PortfolioDashboard() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.portfolioSummary().then(setSummary).catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="alert bad">{error}</div>;
  if (!summary) return <p>Loading portfolio…</p>;

  const g = summary.open_governance;

  return (
    <section>
      <h2>Portfolio Intelligence</h2>
      <div className="stat-row">
        <Stat label="Applications" value={summary.applications_total} />
        <Stat label="Confirmed vetoes" value={g.confirmed_vetoes} tone={g.confirmed_vetoes ? "bad" : "good"} />
        <Stat label="Open divergence" value={g.open_divergence_alerts} tone={g.open_divergence_alerts ? "warn" : "good"} />
        <Stat label="Overrides" value={g.overrides} tone={g.overrides ? "warn" : "good"} />
      </div>

      <div className="grid-2">
        <Breakdown title="By status" data={summary.applications_by_status} />
        <Breakdown title="Decisions by state" data={summary.decisions_by_state} />
      </div>
    </section>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className={`stat ${tone ?? ""}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function Breakdown({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).filter(([, v]) => v > 0);
  return (
    <div className="panel">
      <h4>{title}</h4>
      {entries.length === 0 ? (
        <p className="hint">No records yet.</p>
      ) : (
        <ul className="kv">
          {entries.map(([k, v]) => (
            <li key={k}>
              <span>{k.replace(/_/g, " ")}</span>
              <strong>{v}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
