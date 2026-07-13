"""Tests for the governed decision matrix (PRD 6.7)."""

from __future__ import annotations

from app.domain.enums import DecisionState
from app.modules.rules_engine.decision_matrix import recommend


def test_high_high_strong_is_priority_fund():
    state, note = recommend(merit=8.0, alignment=8.0, evi=8.0)
    assert state is DecisionState.FUND
    assert "Priority" in note


def test_high_low_strong_is_fund_with_conditions():
    state, _ = recommend(merit=8.0, alignment=2.0, evi=8.0)
    assert state is DecisionState.FUND_WITH_CONDITIONS


def test_low_high_strong_is_develop():
    state, _ = recommend(merit=2.0, alignment=8.0, evi=8.0)
    assert state is DecisionState.DEVELOP


def test_high_high_weak_is_defer():
    state, _ = recommend(merit=8.0, alignment=8.0, evi=2.0)
    assert state is DecisionState.DEFER


def test_low_low_any_is_decline():
    assert recommend(merit=2.0, alignment=2.0, evi=8.0)[0] is DecisionState.DECLINE
    assert recommend(merit=2.0, alignment=2.0, evi=2.0)[0] is DecisionState.DECLINE
