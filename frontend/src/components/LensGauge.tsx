import type { IndexResult } from "../types";

const LENS_LABEL: Record<string, string> = {
  sai: "SAI · Allocation",
  ssai: "SSAI · Strategic Alignment",
  ssei: "SSEI · Sustainability & ESG",
  evi: "EVI · Evidence Veracity",
};

// The four lenses are reported independently — never blended (PRD 6, 1.1).
export function LensGauge({ result }: { result: IndexResult }) {
  const pct = Math.round((result.value / 10) * 100);
  const tone = result.value >= 6 ? "good" : result.value >= 4 ? "warn" : "bad";
  return (
    <div className="lens">
      <div className="lens-head">
        <span className="lens-label">{LENS_LABEL[result.lens] ?? result.lens}</span>
        <span className="lens-value">{result.value.toFixed(1)}<small>/10</small></span>
      </div>
      <div className="bar">
        <div className={`bar-fill ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      {result.missing_dimensions.length > 0 && (
        <div className="lens-missing">
          Incomplete: {result.missing_dimensions.length} dimension(s) unscored
        </div>
      )}
    </div>
  );
}
