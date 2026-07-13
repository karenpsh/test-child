// Types mirroring the backend Rules Engine output (app/modules/rules_engine).

export interface IndexResult {
  lens: "sai" | "ssai" | "ssei" | "evi";
  value: number;
  contributions: Record<string, number>;
  methodology_version: string;
  missing_dimensions: string[];
}

export interface DivergenceAlert {
  id: string;
  indicator: string;
  magnitude: number;
  annotation: string | null;
  resolution: string;
}

export interface Veto {
  id: string;
  category: string;
  rationale: string;
  raised_by: string;
  confirmed: boolean;
}

export interface PublicationBlock {
  reason: string;
  detail: string;
}

export interface EvaluationResult {
  sai: IndexResult;
  ssai: IndexResult;
  ssei: IndexResult;
  evi: IndexResult;
  recommended_state: string;
  recommendation_note: string;
  divergence_alerts: DivergenceAlert[];
  confirmed_vetoes: Veto[];
  publication_blocks: PublicationBlock[];
}

export interface PortfolioSummary {
  applications_total: number;
  applications_by_status: Record<string, number>;
  decisions_by_state: Record<string, number>;
  open_governance: {
    confirmed_vetoes: number;
    open_divergence_alerts: number;
    overrides: number;
  };
}

export interface Application {
  id: string;
  applicant_name: string;
  status: string;
  programme_id: string;
}
