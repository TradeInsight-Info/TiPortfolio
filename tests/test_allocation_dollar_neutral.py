"""Tests for DollarNeutral allocation strategy."""

from __future__ import annotations

import pandas as pd
import pytest

from tiportfolio import DollarNeutral


def _row() -> pd.Series:
    return pd.Series({"SPY": 450.0, "AAPL": 180.0, "BIL": 90.0})


def _default_strat() -> DollarNeutral:
    return DollarNeutral(
        long_weights={"SPY": 1.0},
        short_weights={"AAPL": 1.0},
        cash_symbol="BIL",
    )


# ── construction ──────────────────────────────────────────────────────────────

def test_dollar_neutral_get_symbols():
    dn = _default_strat()
    syms = dn.get_symbols()
    assert "SPY" in syms
    assert "AAPL" in syms
    assert "BIL" in syms


def test_dollar_neutral_get_symbols_order():
    dn = DollarNeutral(
        long_weights={"SPY": 0.6, "QQQ": 0.4},
        short_weights={"AAPL": 1.0},
        cash_symbol="BIL",
    )
    syms = dn.get_symbols()
    assert set(syms) == {"SPY", "QQQ", "AAPL", "BIL"}


def test_dollar_neutral_raises_long_sum():
    with pytest.raises(ValueError, match="long_weights must sum to 1.0"):
        DollarNeutral(long_weights={"A": 0.5}, short_weights={"B": 1.0}, cash_symbol="C")


def test_dollar_neutral_raises_short_sum():
    with pytest.raises(ValueError, match="short_weights must sum to 1.0"):
        DollarNeutral(long_weights={"A": 1.0}, short_weights={"B": 0.5}, cash_symbol="C")


def test_dollar_neutral_raises_cash_overlap_with_long():
    with pytest.raises(ValueError, match="cash_symbol"):
        DollarNeutral(long_weights={"A": 1.0}, short_weights={"B": 1.0}, cash_symbol="A")


def test_dollar_neutral_raises_cash_overlap_with_short():
    with pytest.raises(ValueError, match="cash_symbol"):
        DollarNeutral(long_weights={"A": 1.0}, short_weights={"B": 1.0}, cash_symbol="B")


def test_dollar_neutral_raises_long_short_overlap():
    with pytest.raises(ValueError, match="share symbols"):
        DollarNeutral(long_weights={"A": 1.0}, short_weights={"A": 1.0}, cash_symbol="C")


# ── target weights ─────────────────────────────────────────────────────────────

def test_dollar_neutral_target_weights_sum_to_1():
    dn = _default_strat()
    w = dn._target_weights()
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_dollar_neutral_short_symbol_negative():
    dn = _default_strat()
    w = dn._target_weights()
    assert w["AAPL"] < 0.0


def test_dollar_neutral_cash_weight_is_1_for_default_book_size():
    """With book_size=0.5, longs sum to 0.5, shorts sum to -0.5 → cash = 1.0."""
    dn = _default_strat()
    w = dn._target_weights()
    assert abs(w["BIL"] - 1.0) < 1e-9


def test_dollar_neutral_multi_symbol_target_weights():
    dn = DollarNeutral(
        long_weights={"SPY": 0.6, "QQQ": 0.4},
        short_weights={"AAPL": 0.7, "MSFT": 0.3},
        cash_symbol="BIL",
        book_size=0.4,
    )
    w = dn._target_weights()
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert w["AAPL"] < 0 and w["MSFT"] < 0
    assert abs(w["SPY"] - 0.4 * 0.6) < 1e-9
    assert abs(w["AAPL"] - (-0.4 * 0.7)) < 1e-9


# ── initial allocation ────────────────────────────────────────────────────────

def test_dollar_neutral_empty_positions_returns_target():
    dn = _default_strat()
    w = dn.get_target_weights(pd.Timestamp("2020-01-02"), 10_000.0, {}, _row())
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert w["AAPL"] < 0


# ── within-tolerance: no trades ──────────────────────────────────────────────

def test_dollar_neutral_within_tolerance_returns_current():
    """When |long_value - short_value| / equity <= tolerance, returns current weights."""
    dn = _default_strat()
    # long_value = 5000, short_value = 4900, imbalance = 100/10000 = 1% <= 5%
    positions = {"SPY": 5000.0, "AAPL": -4900.0, "BIL": 9900.0}
    equity = sum(positions.values())  # 10_000
    w = dn.get_target_weights(pd.Timestamp("2020-06-01"), equity, positions, _row())
    # Should return current normalized weights, not target
    assert abs(w["SPY"] - positions["SPY"] / equity) < 1e-9


# ── outside-tolerance: rebalance ─────────────────────────────────────────────

def test_dollar_neutral_outside_tolerance_returns_target():
    """When imbalance > tolerance, returns fresh target weights."""
    dn = _default_strat()
    # long_value = 8000, short_value = 2000, imbalance = 6000/10000 = 60% >> 5%
    positions = {"SPY": 8000.0, "AAPL": -2000.0, "BIL": 4000.0}
    equity = sum(positions.values())  # 10_000
    w = dn.get_target_weights(pd.Timestamp("2020-06-01"), equity, positions, _row())
    expected = dn._target_weights()
    assert abs(w["SPY"] - expected["SPY"]) < 1e-9
    assert abs(w["AAPL"] - expected["AAPL"]) < 1e-9


# ── asymmetric book sizing ────────────────────────────────────────────────────

RATIO = 1.135


def test_dollar_neutral_asymmetric_txn_kvue_ratio():
    """long_book_size / short_book_size produces correct 1:1.135 TXN:KVUE weight ratio."""
    lbs = 1.0 / (1.0 + RATIO)
    sbs = RATIO / (1.0 + RATIO)
    dn = DollarNeutral(
        long_weights={"TXN": 1.0},
        short_weights={"KVUE": 1.0},
        cash_symbol="BIL",
        long_book_size=lbs,
        short_book_size=sbs,
    )
    w = dn._target_weights()
    assert abs(w["TXN"] / abs(w["KVUE"]) - 1.0 / RATIO) < 1e-9
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_dollar_neutral_asymmetric_weights_sum_to_1():
    """Asymmetric book sizes still produce target weights that sum to 1.0."""
    dn = DollarNeutral(
        long_weights={"A": 1.0},
        short_weights={"B": 1.0},
        cash_symbol="C",
        long_book_size=0.3,
        short_book_size=0.7,
    )
    w = dn._target_weights()
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert abs(w["A"] - 0.3) < 1e-9
    assert abs(w["B"] - (-0.7)) < 1e-9
    assert abs(w["C"] - 1.4) < 1e-9  # 1.0 - (0.3 - 0.7) = 1.4


def test_dollar_neutral_none_per_side_falls_back_to_book_size():
    """Omitting long_book_size and short_book_size falls back to book_size (backward compat)."""
    dn = DollarNeutral(
        long_weights={"A": 1.0},
        short_weights={"B": 1.0},
        cash_symbol="C",
        book_size=0.4,
    )
    w = dn._target_weights()
    assert abs(w["A"] - 0.4) < 1e-9
    assert abs(w["B"] - (-0.4)) < 1e-9


# ── public import ─────────────────────────────────────────────────────────────

def test_dollar_neutral_public_import():
    from tiportfolio import DollarNeutral as DN  # noqa: F401
    assert DN is not None
