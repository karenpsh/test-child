"""ETTL Conviction Index (ECI) — the MBAN Gold Standard formulas.

Implements the Council-Weighted logic from the ECI Methodology:

* **WIR** — Council-Weighted Index Rating, the primary cohort-ranking metric.
  ``WIR = LiveAvg × 0.40 + CouncilAvg × 0.60``. Council auditors anchor 60%
  so a high-conviction rating in January equals one in December.
* **CDA** — Council-Divergence Alert. ``|LiveAvg − CouncilAvg|``; > 1.5 means
  the venture won the pitch but failed the audit.
* **DAI** — Divergence Alert Index. Population standard deviation across all
  judges, ``√(Σ(xᵢ − μ)² / n)``; threshold 1.5 at the gold-standard panel of
  four, tightened to 1.0 when the panel drops to three.
* **ACD** — Angel Conviction Delta. ``|TechnicalFeasibility − CommercialReadiness|``;
  > 2.0 signals a venture that is technically sound but commercially unready.

Doctrine carried over from the methodology: divergence is surfaced and
annotated, never averaged away — a 2-vs-2 deadlock is a strategic discovery,
not a data problem. All functions here are deterministic and reproducible from
stored judge scores; no AI participates.
"""

from __future__ import annotations

from enum import Enum
from statistics import fmean, pstdev

from pydantic import BaseModel, Field


class JudgeType(str, Enum):
    """The 2+2 Gold Standard panel composition."""

    LIVE_TIGER = "live_tiger"  # guest judges — market pulse
    COUNCIL_AUDITOR = "council_auditor"  # permanent institutional auditors


class PitchMode(str, Enum):
    """How the panel observed the founders (chemistry is judged by humans)."""

    LIVE = "live"
    VIDEO = "video"  # 5-minute recorded presentation fallback


class JudgeScore(BaseModel):
    """One judge's result for one venture.

    ``overall`` is the judge's weighted-normalised total from the 10-dimension
    scoring sheet (0–10). The two named dimensions are carried separately
    because ACD is computed from them.
    """

    judge_id: str
    judge_type: JudgeType
    overall: float = Field(ge=0, le=10)
    technical_feasibility: float | None = Field(default=None, ge=0, le=10)
    commercial_readiness: float | None = Field(default=None, ge=0, le=10)
    conviction: bool | None = Field(
        default=None, description="Fund / no-fund vote, when the panel takes one."
    )


class ECIConfig(BaseModel):
    """Versioned methodology constants. Defaults are the MBAN Gold Standard."""

    live_weight: float = 0.40
    council_weight: float = 0.60
    cda_threshold: float = 1.5
    dai_threshold: float = 1.5  # gold-standard panel of four
    dai_threshold_panel_of_three: float = 1.0  # tightened per the methodology
    acd_threshold: float = 2.0
    min_panel: int = 3
    gold_standard_panel: int = 4


class ECIAlert(BaseModel):
    code: str
    detail: str


class ECIResult(BaseModel):
    """Everything the executive brief needs, reproducible from stored scores."""

    panel_size: int
    pitch_mode: PitchMode
    live_avg: float
    council_avg: float
    wir: float
    cda: float
    dai: float
    dai_threshold_applied: float
    acd: float | None
    alerts: list[ECIAlert]

    @property
    def clean(self) -> bool:
        return not self.alerts


def compute_eci(
    scores: list[JudgeScore],
    *,
    pitch_mode: PitchMode = PitchMode.LIVE,
    config: ECIConfig | None = None,
) -> ECIResult:
    """Run the full ECI computation for one venture's panel.

    Raises ``ValueError`` for panels below mathematical defensibility (fewer
    than three judges, or missing either judge type — WIR needs both anchors).
    """

    cfg = config or ECIConfig()

    if len(scores) < cfg.min_panel:
        raise ValueError(
            f"Panel of {len(scores)} is below mathematical defensibility; "
            f"minimum is {cfg.min_panel}, gold standard is {cfg.gold_standard_panel} (2+2)."
        )

    live = [s.overall for s in scores if s.judge_type is JudgeType.LIVE_TIGER]
    council = [s.overall for s in scores if s.judge_type is JudgeType.COUNCIL_AUDITOR]
    if not live or not council:
        raise ValueError(
            "WIR requires both live tigers and council auditors on the panel; "
            "the council anchor cannot be computed without auditors."
        )

    live_avg = fmean(live)
    council_avg = fmean(council)
    wir = cfg.live_weight * live_avg + cfg.council_weight * council_avg
    cda = abs(live_avg - council_avg)
    dai = pstdev([s.overall for s in scores])
    dai_threshold = (
        cfg.dai_threshold_panel_of_three if len(scores) == 3 else cfg.dai_threshold
    )

    acd: float | None = None
    tech = [s.technical_feasibility for s in scores if s.technical_feasibility is not None]
    comm = [s.commercial_readiness for s in scores if s.commercial_readiness is not None]
    if tech and comm:
        acd = abs(fmean(tech) - fmean(comm))

    alerts: list[ECIAlert] = []

    if cda > cfg.cda_threshold:
        side = (
            "won the pitch but failed the audit"
            if live_avg > council_avg
            else "audited above its pitch — council sees more than the room did"
        )
        alerts.append(
            ECIAlert(
                code="cda",
                detail=f"CDA {cda:.2f} > {cfg.cda_threshold}: {side}. Investigate and annotate.",
            )
        )

    if dai > dai_threshold:
        alerts.append(
            ECIAlert(
                code="dai",
                detail=(
                    f"DAI {dai:.2f} > {dai_threshold} (panel of {len(scores)}): "
                    "expert conflict / volatility — hidden risk or disruptive potential."
                ),
            )
        )

    if acd is not None and acd > cfg.acd_threshold:
        direction = (
            "technically sound but commercially unready"
            if fmean(tech) > fmean(comm)
            else "commercially polished but technically thin"
        )
        alerts.append(
            ECIAlert(
                code="acd",
                detail=f"ACD {acd:.2f} > {cfg.acd_threshold}: {direction}.",
            )
        )

    votes = [s.conviction for s in scores if s.conviction is not None]
    if len(votes) == len(scores) == cfg.gold_standard_panel:
        if sum(votes) == cfg.gold_standard_panel // 2:
            alerts.append(
                ECIAlert(
                    code="deadlock_2v2",
                    detail=(
                        "2-vs-2 deadlock: strategic discovery — the venture is "
                        "polarising, a pattern that often precedes disruption. "
                        "Surface to the CIO; do not average away."
                    ),
                )
            )

    return ECIResult(
        panel_size=len(scores),
        pitch_mode=pitch_mode,
        live_avg=round(live_avg, 4),
        council_avg=round(council_avg, 4),
        wir=round(wir, 4),
        cda=round(cda, 4),
        dai=round(dai, 4),
        dai_threshold_applied=dai_threshold,
        acd=round(acd, 4) if acd is not None else None,
        alerts=alerts,
    )
