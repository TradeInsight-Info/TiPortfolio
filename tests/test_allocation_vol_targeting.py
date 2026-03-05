"""Tests for VolatilityTargeting allocation strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tiportfolio import VolatilityTargeting


def _make_prices(symbols: list[str], n: int, daily_vols: dict[str, float] | None = None, seed: int = 0) -> pd.DataFrame:
    """Synthetic prices with controllable per-asset daily volatility."""
    rng = np.random.default_rng(seed)
    if daily_vols is None:
        daily_vols = {s: 0.01 for s in symbols}
    dates = pd.date_range("2020-01-02", periods=n, freq="B", tz="UTC")
    data: dict[str, list[float]] = {}
    for s in symbols:
        vol = daily_vols.get(s, 0.01)
        returns = rng.normal(0.0, vol, n)
        prices = 100.0 * np.cumprod(1.0 + returns)
        data[s] = prices.tolist()
    return pd.DataFrame(data, index=dates)


# ── construction ──────────────────────────────────────────────────────────────

def test_vol_targeting_get_symbols():
    vt = VolatilityTargeting(symbols=["A", "B", "C"], lookback_days=20)
    assert vt.get_symbols() == ["A", "B", "C"]


# ── inverse-vol weights ───────────────────────────────────────────────────────

def test_vol_targeting_weights_sum_to_1():
    """Normalized inverse-vol weights sum to 1.0."""
    vt = VolatilityTargeting(symbols=["A", "B"], lookback_days=20)
    prices_history = _make_prices(["A", "B"], n=25, daily_vols={"A": 0.01, "B": 0.02})
    row = pd.Series({"A": 100.0, "B": 100.0})
    w = vt.get_target_weights(prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history)
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_vol_targeting_higher_vol_gets_lower_weight():
    """Asset B has 2x daily vol of A → weight_A > weight_B."""
    vt = VolatilityTargeting(symbols=["A", "B"], lookback_days=20)
    # Use many rows so realized vol is stable
    prices_history = _make_prices(["A", "B"], n=60, daily_vols={"A": 0.005, "B": 0.02}, seed=42)
    row = pd.Series({"A": 100.0, "B": 100.0})
    w = vt.get_target_weights(prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history)
    assert w["A"] > w["B"], f"Expected w_A({w['A']:.3f}) > w_B({w['B']:.3f})"


# ── target_vol scaling ────────────────────────────────────────────────────────

def test_vol_targeting_target_vol_scales_down_when_above():
    """When portfolio_vol > target_vol, scalar < 1 → sum(weights) < 1."""
    # daily_vol ≈ 2% → annualized ≈ 31.7% >> target_vol=0.10
    vt = VolatilityTargeting(symbols=["A", "B"], lookback_days=20, target_vol=0.10)
    prices_history = _make_prices(["A", "B"], n=25, daily_vols={"A": 0.02, "B": 0.02}, seed=7)
    row = pd.Series({"A": 100.0, "B": 100.0})
    w = vt.get_target_weights(prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history)
    total = sum(w.values())
    assert total < 1.0 - 1e-6, f"Expected total < 1.0; got {total:.4f}"


def test_vol_targeting_target_vol_unchanged_when_below():
    """When portfolio_vol < target_vol, weights stay normalized (sum to 1.0)."""
    # daily_vol ≈ 0.01% → annualized ≈ 0.16% << target_vol=0.50
    vt = VolatilityTargeting(symbols=["A", "B"], lookback_days=20, target_vol=0.50)
    prices_history = _make_prices(["A", "B"], n=25, daily_vols={"A": 0.0001, "B": 0.0001}, seed=3)
    row = pd.Series({"A": 100.0, "B": 100.0})
    w = vt.get_target_weights(prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history)
    assert abs(sum(w.values()) - 1.0) < 1e-9


# ── fallbacks ─────────────────────────────────────────────────────────────────

def test_vol_targeting_fallback_no_context():
    """Returns equal weights when prices_history not in context."""
    vt = VolatilityTargeting(symbols=["A", "B"], lookback_days=20)
    row = pd.Series({"A": 100.0, "B": 100.0})
    with pytest.warns(UserWarning):
        w = vt.get_target_weights(pd.Timestamp("2020-01-02", tz="UTC"), 10_000.0, {}, row)
    assert w == {"A": 0.5, "B": 0.5}


def test_vol_targeting_fallback_insufficient_rows():
    """Returns equal weights when history has fewer than lookback_days + 1 rows."""
    vt = VolatilityTargeting(symbols=["A", "B"], lookback_days=20)
    prices_history = _make_prices(["A", "B"], n=5)  # only 5 rows < 21
    row = pd.Series({"A": 100.0, "B": 100.0})
    with pytest.warns(UserWarning):
        w = vt.get_target_weights(prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history)
    assert w == {"A": 0.5, "B": 0.5}


# ── public import ─────────────────────────────────────────────────────────────

def test_vol_targeting_public_import():
    from tiportfolio import VolatilityTargeting as VT  # noqa: F401
    assert VT is not None
