"""Tests for BetaScreenerStrategy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tiportfolio import BetaScreenerStrategy


def _make_universe_prices(
    symbols: list[str],
    betas: dict[str, float],
    n: int = 120,
    seed: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthetic prices with known betas relative to benchmark.

    Returns (prices_history, benchmark_prices) where each asset return ≈ beta_i * bench_return.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-02", periods=n, freq="B", tz="UTC")
    bench_ret = rng.normal(0.0, 0.01, n)
    bench_prices = 100.0 * np.cumprod(1.0 + bench_ret)

    data: dict[str, list[float]] = {}
    for s in symbols:
        b = betas.get(s, 1.0)
        noise = rng.normal(0.0, 0.001, n)
        r = b * bench_ret + noise
        data[s] = (100.0 * np.cumprod(1.0 + r)).tolist()

    prices_history = pd.DataFrame(data, index=dates)
    bench_df = pd.DataFrame(
        {"open": bench_prices, "high": bench_prices, "low": bench_prices,
         "close": bench_prices, "volume": np.ones(n)},
        index=dates,
    )
    return prices_history, bench_df


UNIVERSE = ["A", "B", "C", "D", "E", "F"]
BETAS = {"A": 0.2, "B": 0.5, "C": 0.8, "D": 1.2, "E": 1.5, "F": 2.0}


def _default_strat(n_long: int = 2, n_short: int = 2) -> tuple[BetaScreenerStrategy, pd.DataFrame, pd.DataFrame]:
    ph, bp = _make_universe_prices(UNIVERSE, BETAS, n=120)
    strat = BetaScreenerStrategy(
        universe=UNIVERSE,
        n_long=n_long,
        n_short=n_short,
        cash_symbol="CASH",
        benchmark_prices=bp,
        lookback_days=60,
    )
    return strat, ph, bp


# ── construction ──────────────────────────────────────────────────────────────

def test_get_symbols_returns_universe_plus_cash():
    strat, _, _ = _default_strat()
    syms = strat.get_symbols()
    assert set(syms) == set(UNIVERSE) | {"CASH"}
    assert "CASH" in syms


def test_get_symbols_excludes_benchmark():
    strat, _, _ = _default_strat()
    assert "SPY" not in strat.get_symbols()


def test_raises_cash_in_universe():
    _, _, bp = _default_strat()
    with pytest.raises(ValueError, match="cash_symbol"):
        BetaScreenerStrategy(
            universe=["A", "CASH"],
            n_long=1, n_short=1, cash_symbol="CASH",
            benchmark_prices=bp,
        )


def test_raises_n_long_plus_n_short_exceeds_universe():
    _, _, bp = _default_strat()
    with pytest.raises(ValueError, match="exceeds universe"):
        BetaScreenerStrategy(
            universe=["A", "B"],
            n_long=1, n_short=2, cash_symbol="CASH",
            benchmark_prices=bp,
        )


# ── beta selection ────────────────────────────────────────────────────────────

def test_long_book_holds_lowest_beta():
    """Lowest-beta symbols (A, B) land in the long book with positive weights."""
    strat, ph, _ = _default_strat(n_long=2, n_short=2)
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    w = strat.get_target_weights(ph.index[-1], 10_000.0, {}, row, prices_history=ph)
    # A and B are the two lowest-beta; they should have positive weights
    assert w["A"] > 0
    assert w["B"] > 0


def test_short_book_holds_highest_beta():
    """Highest-beta symbols (E, F) land in the short book with negative weights."""
    strat, ph, _ = _default_strat(n_long=2, n_short=2)
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    w = strat.get_target_weights(ph.index[-1], 10_000.0, {}, row, prices_history=ph)
    assert w["E"] < 0
    assert w["F"] < 0


def test_unselected_symbols_are_zero():
    """Symbols not in long or short book have zero weight."""
    strat, ph, _ = _default_strat(n_long=2, n_short=2)
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    w = strat.get_target_weights(ph.index[-1], 10_000.0, {}, row, prices_history=ph)
    # C and D are mid-beta and should be 0
    assert w["C"] == 0.0
    assert w["D"] == 0.0


# ── beta neutrality ───────────────────────────────────────────────────────────

def test_portfolio_beta_approximately_zero():
    """sum(w_i * beta_i) ≈ 0 for selected symbols."""
    strat, ph, bp = _default_strat(n_long=2, n_short=2)
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    w = strat.get_target_weights(ph.index[-1], 10_000.0, {}, row, prices_history=ph)

    # Compute realized betas from same window
    betas = strat._compute_betas(ph)
    assert betas is not None
    port_beta = sum(w[s] * betas[s] for s in UNIVERSE)
    assert abs(port_beta) < 0.15, f"Portfolio beta {port_beta:.4f} not near zero"


def test_weights_sum_to_1():
    strat, ph, _ = _default_strat()
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    w = strat.get_target_weights(ph.index[-1], 10_000.0, {}, row, prices_history=ph)
    assert abs(sum(w.values()) - 1.0) < 1e-9


# ── fallbacks ─────────────────────────────────────────────────────────────────

def test_fallback_no_prices_history():
    strat, _, _ = _default_strat()
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    with pytest.warns(UserWarning):
        w = strat.get_target_weights(pd.Timestamp("2020-01-02", tz="UTC"), 10_000.0, {}, row)
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_fallback_insufficient_history():
    strat, ph, _ = _default_strat()
    short_ph = ph.iloc[:10]  # only 10 rows < lookback_days + 1 = 61
    row = pd.Series({s: 100.0 for s in UNIVERSE} | {"CASH": 1.0})
    with pytest.warns(UserWarning):
        w = strat.get_target_weights(short_ph.index[-1], 10_000.0, {}, row, prices_history=short_ph)
    assert abs(sum(w.values()) - 1.0) < 1e-9


# ── public import ─────────────────────────────────────────────────────────────

def test_public_import():
    from tiportfolio import BetaScreenerStrategy as BSS  # noqa: F401
    assert BSS is not None
