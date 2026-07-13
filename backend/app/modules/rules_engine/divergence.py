"""Divergence indicators (PRD 10.1).

Material divergence must raise an alert and block committee finalisation until
resolved (PRD 8.4, acceptance criterion 7). These functions only *detect*
divergence; resolution is a governed human workflow.
"""

from __future__ import annotations

from statistics import fmean

from app.domain.enums import Role
from app.domain.models import DivergenceAlert, Scorecard


def _mean_scorecard_value(sc: Scorecard) -> float:
    """Unweighted mean of a scorecard's dimension scores (0-10)."""

    if not sc.dimension_scores:
        return 0.0
    return fmean(s.score for s in sc.dimension_scores)


def technical_commercial_divergence(technical: float, commercial: float) -> float:
    """|Technical score - Commercial score| (PRD 10.1)."""

    return abs(technical - commercial)


def programme_expert_divergence(programme_avg: float, expert_avg: float) -> float:
    """|Programme average - Independent expert average| (PRD 10.1)."""

    return abs(programme_avg - expert_avg)


def funding_confidence_delta(merit: float, financial_stewardship: float) -> float:
    """|Merit score - Financial stewardship score| (PRD 10.1)."""

    return abs(merit - financial_stewardship)


def policy_commercial_delta(strategic_alignment: float, commercial_readiness: float) -> float:
    """|Strategic alignment - Commercial readiness| (PRD 10.1)."""

    return abs(strategic_alignment - commercial_readiness)


def individual_outliers(scorecards: list[Scorecard], threshold: float) -> list[DivergenceAlert]:
    """Flag assessors whose overall mean deviates from the panel mean by more
    than ``threshold`` (default 3.0/10, PRD 10.1)."""

    submitted = [sc for sc in scorecards if sc.submitted]
    if len(submitted) < 2:
        return []
    means = {sc.assessor_id: _mean_scorecard_value(sc) for sc in submitted}
    panel_mean = fmean(means.values())
    alerts: list[DivergenceAlert] = []
    for assessor_id, mean in means.items():
        magnitude = abs(mean - panel_mean)
        if magnitude > threshold:
            alerts.append(
                DivergenceAlert(
                    indicator=f"individual_outlier:{assessor_id}",
                    magnitude=round(magnitude, 4),
                )
            )
    return alerts


def detect_all(
    scorecards: list[Scorecard],
    threshold: float,
    *,
    material_threshold: float = 3.0,
) -> list[DivergenceAlert]:
    """Compute the panel-level divergence indicators plus individual outliers.

    Role means are derived from submitted scorecards. An indicator only becomes
    an alert when its magnitude meets ``material_threshold``; sub-threshold
    divergence is not surfaced as blocking.
    """

    submitted = [sc for sc in scorecards if sc.submitted]
    alerts: list[DivergenceAlert] = list(individual_outliers(scorecards, threshold))

    def role_mean(role: Role) -> float | None:
        vals = [_mean_scorecard_value(sc) for sc in submitted if sc.role == role]
        return fmean(vals) if vals else None

    technical = role_mean(Role.TECHNICAL_ASSESSOR)
    commercial = role_mean(Role.COMMERCIAL_ASSESSOR)
    financial = role_mean(Role.FINANCIAL_ASSESSOR)

    if technical is not None and commercial is not None:
        mag = technical_commercial_divergence(technical, commercial)
        if mag >= material_threshold:
            alerts.append(DivergenceAlert(indicator="technical_commercial", magnitude=round(mag, 4)))

    if technical is not None and financial is not None:
        # Merit proxied by technical credibility for this panel-level check.
        mag = funding_confidence_delta(technical, financial)
        if mag >= material_threshold:
            alerts.append(DivergenceAlert(indicator="funding_confidence", magnitude=round(mag, 4)))

    return alerts
