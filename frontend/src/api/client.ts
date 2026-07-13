// Thin API client for the SAGE backend.
import type { Application, EvaluationResult, PortfolioSummary } from "../types";

const BASE = "/api/v1";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listApplications: () => get<Application[]>("/applications"),
  decisionCard: (applicationId: string) =>
    get<EvaluationResult>(`/committee/applications/${applicationId}/decision-card`),
  portfolioSummary: () => get<PortfolioSummary>("/portfolio/summary"),
};
