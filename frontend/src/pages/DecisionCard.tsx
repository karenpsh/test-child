import { useEffect, useState } from "react";
import { api } from "../api/client";
import { LensGauge } from "../components/LensGauge";
import type { Application, EvaluationResult } from "../types";

// One standard decision card per applicant (PRD 8.5, acceptance criterion 9).
export function DecisionCard() {
  const [apps, setApps] = useState<Application[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [card, setCard] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listApplications().then(setApps).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setCard(null);
    api.decisionCard(selected).then(setCard).catch((e) => setError(String(e)));
  }, [selected]);

  return (
    <section>
      <h2>Committee Decision Card</h2>
      <p className="hint">
        A structured card — SAI, SSAI, SSEI, EVI, vetoes and publication blocks — not a document dump.
      </p>

      <label className="field">
        Application
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Select an application…</option>
          {apps.map((a) => (
            <option key={a.id} value={a.id}>
              {a.applicant_name} · {a.status}
            </option>
          ))}
        </select>
      </label>

      {error && <div className="alert bad">{error}</div>}

      {card && (
        <div className="card">
          <div className="lenses">
            <LensGauge result={card.sai} />
            <LensGauge result={card.ssai} />
            <LensGauge result={card.ssei} />
            <LensGauge result={card.evi} />
          </div>

          <div className="recommendation">
            <span className="rec-label">Recommended</span>
            <span className={`rec-state ${card.publication_blocks.length ? "blocked" : "clear"}`}>
              {card.recommended_state.replace(/_/g, " ")}
            </span>
            <span className="rec-note">{card.recommendation_note}</span>
          </div>

          {card.confirmed_vetoes.length > 0 && (
            <div className="alert bad">
              <strong>Confirmed vetoes:</strong>{" "}
              {card.confirmed_vetoes.map((v) => v.category).join(", ")} — approval is barred.
            </div>
          )}

          {card.publication_blocks.length > 0 ? (
            <div className="alert warn">
              <strong>Publication blocked:</strong>
              <ul>
                {card.publication_blocks.map((b) => (
                  <li key={b.reason}>{b.detail}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="alert good">No publication blocks — decision may be recorded.</div>
          )}

          {card.divergence_alerts.length > 0 && (
            <div className="divergence">
              <h4>Divergence alerts</h4>
              <ul>
                {card.divergence_alerts.map((d) => (
                  <li key={d.id}>
                    {d.indicator} · magnitude {d.magnitude.toFixed(1)} · {d.resolution}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="method">Methodology {card.sai.methodology_version}</p>
        </div>
      )}
    </section>
  );
}
