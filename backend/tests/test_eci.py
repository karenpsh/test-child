"""Tests for the ECI (ETTL Conviction Index) formulas — MBAN Gold Standard."""

from __future__ import annotations

import math

import pytest

from app.modules.rules_engine.eci import (
    ECIConfig,
    JudgeScore,
    JudgeType,
    PitchMode,
    compute_eci,
)


def _judge(jid, jtype, overall, tech=None, comm=None, vote=None):
    return JudgeScore(
        judge_id=jid,
        judge_type=jtype,
        overall=overall,
        technical_feasibility=tech,
        commercial_readiness=comm,
        conviction=vote,
    )


def _panel(t1, t2, a1, a2, **kw):
    """Gold-standard 2+2 panel: two live tigers, two council auditors."""
    return [
        _judge("tiger-1", JudgeType.LIVE_TIGER, t1, **kw),
        _judge("tiger-2", JudgeType.LIVE_TIGER, t2, **kw),
        _judge("auditor-1", JudgeType.COUNCIL_AUDITOR, a1, **kw),
        _judge("auditor-2", JudgeType.COUNCIL_AUDITOR, a2, **kw),
    ]


def test_wir_council_weighted_40_60():
    # Live avg 8.0, council avg 6.0 -> WIR = 0.4*8 + 0.6*6 = 6.8
    result = compute_eci(_panel(8.0, 8.0, 6.0, 6.0))
    assert result.wir == 6.8
    assert result.live_avg == 8.0
    assert result.council_avg == 6.0


def test_cda_alert_won_pitch_failed_audit():
    # Live 8.0 vs council 6.0 -> CDA 2.0 > 1.5
    result = compute_eci(_panel(8.0, 8.0, 6.0, 6.0))
    codes = {a.code for a in result.alerts}
    assert "cda" in codes
    assert any("won the pitch but failed the audit" in a.detail for a in result.alerts)


def test_cda_within_threshold_is_clean():
    result = compute_eci(_panel(7.0, 7.5, 6.5, 7.0))
    assert all(a.code != "cda" for a in result.alerts)


def test_dai_is_population_std_dev():
    scores = [8.0, 8.0, 6.0, 6.0]
    result = compute_eci(_panel(*scores))
    mu = sum(scores) / 4
    expected = math.sqrt(sum((x - mu) ** 2 for x in scores) / 4)
    assert result.dai == pytest.approx(expected, abs=1e-4)
    assert result.dai == pytest.approx(1.0, abs=1e-9)  # sanity: σ of 8,8,6,6 is 1.0
    # 1.0 is below the n=4 threshold of 1.5 -> no DAI alert
    assert all(a.code != "dai" for a in result.alerts)


def test_dai_threshold_tightens_on_panel_of_three():
    # σ of 8,8,5.2 ≈ 1.32 — above the tightened 1.0 but below the n=4 threshold 1.5.
    three = [
        _judge("tiger-1", JudgeType.LIVE_TIGER, 8.0),
        _judge("tiger-2", JudgeType.LIVE_TIGER, 8.0),
        _judge("auditor-1", JudgeType.COUNCIL_AUDITOR, 5.2),
    ]
    result = compute_eci(three)
    assert result.dai_threshold_applied == 1.0
    assert any(a.code == "dai" for a in result.alerts)


def test_acd_flags_overengineering():
    panel = _panel(7.0, 7.0, 7.0, 7.0, tech=9.0, comm=5.0)
    result = compute_eci(panel)
    assert result.acd == 4.0
    assert any(
        a.code == "acd" and "technically sound but commercially unready" in a.detail
        for a in result.alerts
    )


def test_deadlock_2v2_is_strategic_discovery():
    panel = [
        _judge("tiger-1", JudgeType.LIVE_TIGER, 8.0, vote=True),
        _judge("tiger-2", JudgeType.LIVE_TIGER, 7.5, vote=True),
        _judge("auditor-1", JudgeType.COUNCIL_AUDITOR, 6.8, vote=False),
        _judge("auditor-2", JudgeType.COUNCIL_AUDITOR, 7.0, vote=False),
    ]
    result = compute_eci(panel)
    assert any(a.code == "deadlock_2v2" for a in result.alerts)


def test_panel_below_three_rejected():
    with pytest.raises(ValueError, match="mathematical defensibility"):
        compute_eci(
            [
                _judge("tiger-1", JudgeType.LIVE_TIGER, 8.0),
                _judge("auditor-1", JudgeType.COUNCIL_AUDITOR, 7.0),
            ]
        )


def test_panel_without_council_anchor_rejected():
    with pytest.raises(ValueError, match="council"):
        compute_eci(
            [
                _judge("tiger-1", JudgeType.LIVE_TIGER, 8.0),
                _judge("tiger-2", JudgeType.LIVE_TIGER, 7.0),
                _judge("tiger-3", JudgeType.LIVE_TIGER, 7.5),
            ]
        )


def test_video_fallback_mode_recorded():
    result = compute_eci(_panel(7.0, 7.0, 7.0, 7.0), pitch_mode=PitchMode.VIDEO)
    assert result.pitch_mode is PitchMode.VIDEO


def test_config_is_overridable_methodology_versioning():
    cfg = ECIConfig(cda_threshold=0.5)
    result = compute_eci(_panel(7.5, 7.5, 6.8, 6.8), config=cfg)
    assert any(a.code == "cda" for a in result.alerts)
