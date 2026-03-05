"""Tests for BetaNeutral allocation strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tiportfolio import BetaNeutral


def _make_beta_prices(
    long_symbols: list[str],
    short_symbols: list[str],
    betas: dict[str, float],
    n: int = 120,
    seed: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (prices_history, benchmark_prices) with synthetic returns at known betas.

    Each asset return = beta_i * bench_return + idio_noise (small noise).
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-02", periods=n, freq="B", tz="UTC")

    bench_returns = rng.normal(0.0, 0.01, n)
    bench_prices = 100.0 * np.cumprod(1.0 + bench_returns)

    all_syms = long_symbols + short_symbols
    data: dict[str, list[float]] = {}
    for s in all_syms:
        b = betas.get(s, 1.0)
        noise = rng.normal(0.0, 0.001, n)
        r = b * bench_returns + noise
        data[s] = (100.0 * np.cumprod(1.0 + r)).tolist()

    prices_history = pd.DataFrame(data, index=dates)

    # benchmark_prices as OHLCV DataFrame (same dates)
    bp = pd.DataFrame(
        {
            "open": bench_prices * 0.999,
            "high": bench_prices * 1.001,
            "low": bench_prices * 0.998,
            "close": bench_prices,
            "volume": np.ones(n) * 1_000_000,
        },
        index=dates,
    )
    return prices_history, bp


# ── construction ──────────────────────────────────────────────────────────────

def test_beta_neutral_get_symbols_no_benchmark():
    bn = BetaNeutral(long_symbols=["A"], short_symbols=["B"], cash_symbol="C", benchmark_symbol="SPY")
    syms = bn.get_symbols()
    assert set(syms) == {"A", "B", "C"}
    assert "SPY" not in syms


def test_beta_neutral_raises_overlap_long_short():
    with pytest.raises(ValueError, match="share symbols"):
        BetaNeutral(long_symbols=["A"], short_symbols=["A"], cash_symbol="C")


def test_beta_neutral_raises_cash_in_long():
    with pytest.raises(ValueError, match="cash_symbol"):
        BetaNeutral(long_symbols=["A", "C"], short_symbols=["B"], cash_symbol="C")


def test_beta_neutral_raises_cash_in_short():
    with pytest.raises(ValueError, match="cash_symbol"):
        BetaNeutral(long_symbols=["A"], short_symbols=["B", "C"], cash_symbol="C")


# ── pre-loaded benchmark_prices bypasses fetch ────────────────────────────────

def test_beta_neutral_preloaded_benchmark_used():
    """With benchmark_prices set, no external fetch occurs and betas are computed."""
    prices_history, bp = _make_beta_prices(["A"], ["B"], betas={"A": 1.2, "B": 0.8}, n=80)
    bn = BetaNeutral(
        long_symbols=["A"],
        short_symbols=["B"],
        cash_symbol="C",
        benchmark_prices=bp,
        lookback_days=60,
    )
    row = prices_history.iloc[-1].reindex(["A", "B"])
    # Add cash column with dummy price
    row["C"] = 100.0
    w = bn.get_target_weights(
        prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history
    )
    assert "A" in w and "B" in w and "C" in w
    assert "SPY" not in w


# ── two-symbol beta neutral ───────────────────────────────────────────────────

def test_beta_neutral_two_symbol_zero_portfolio_beta():
    """sum(w_i * beta_i) ≈ 0 for two-symbol beta-neutral with known betas."""
    long_syms = ["A"]
    short_syms = ["B"]
    betas = {"A": 1.5, "B": 0.5}
    prices_history, bp = _make_beta_prices(long_syms, short_syms, betas=betas, n=120)

    bn = BetaNeutral(
        long_symbols=long_syms,
        short_symbols=short_syms,
        cash_symbol="CASH",
        benchmark_prices=bp,
        lookback_days=60,
    )
    row = pd.Series({"A": 100.0, "B": 100.0, "CASH": 1.0})
    w = bn.get_target_weights(
        prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history
    )
    # Compute realized betas from the same lookback window
    hist = prices_history.tail(61)
    sym_rets = hist.pct_change().dropna()
    bench_rets = bp["close"].reindex(hist.index).pct_change().dropna()
    common = sym_rets.index.intersection(bench_rets.index)
    bench_var = bench_rets.loc[common].var()
    beta_A = sym_rets["A"].loc[common].cov(bench_rets.loc[common]) / bench_var
    beta_B = sym_rets["B"].loc[common].cov(bench_rets.loc[common]) / bench_var

    portfolio_beta = w["A"] * beta_A + w["B"] * beta_B
    assert abs(portfolio_beta) < 0.05, f"Portfolio beta {portfolio_beta:.4f} not near zero"


def test_beta_neutral_weights_sum_to_1():
    """Total weights (long + short + cash) sum to 1.0."""
    prices_history, bp = _make_beta_prices(["A"], ["B"], betas={"A": 1.2, "B": 0.6}, n=80)
    bn = BetaNeutral(
        long_symbols=["A"],
        short_symbols=["B"],
        cash_symbol="CASH",
        benchmark_prices=bp,
        lookback_days=60,
    )
    row = pd.Series({"A": 100.0, "B": 100.0, "CASH": 1.0})
    w = bn.get_target_weights(
        prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history
    )
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_beta_neutral_benchmark_not_in_weights():
    """benchmark_symbol must NOT appear in returned weights."""
    prices_history, bp = _make_beta_prices(["A"], ["B"], betas={"A": 1.0, "B": 0.5}, n=80)
    bn = BetaNeutral(
        long_symbols=["A"],
        short_symbols=["B"],
        cash_symbol="CASH",
        benchmark_symbol="MYBENCH",
        benchmark_prices=bp,
        lookback_days=60,
    )
    row = pd.Series({"A": 100.0, "B": 100.0, "CASH": 1.0})
    w = bn.get_target_weights(
        prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history
    )
    assert "MYBENCH" not in w


# ── fallbacks ─────────────────────────────────────────────────────────────────

def test_beta_neutral_fallback_no_prices_history():
    """Returns equal-weight fallback when prices_history not in context."""
    bn = BetaNeutral(long_symbols=["A"], short_symbols=["B"], cash_symbol="C", lookback_days=60)
    row = pd.Series({"A": 100.0, "B": 100.0, "C": 1.0})
    with pytest.warns(UserWarning):
        w = bn.get_target_weights(pd.Timestamp("2020-01-02", tz="UTC"), 10_000.0, {}, row)
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert w["A"] > 0 and w["B"] < 0


def test_beta_neutral_fallback_insufficient_history():
    """Returns equal-weight fallback when history rows < lookback_days + 1."""
    _, bp = _make_beta_prices(["A"], ["B"], betas={"A": 1.0, "B": 0.5}, n=80)
    bn = BetaNeutral(
        long_symbols=["A"],
        short_symbols=["B"],
        cash_symbol="C",
        benchmark_prices=bp,
        lookback_days=60,
    )
    prices_history, _ = _make_beta_prices(["A"], ["B"], betas={"A": 1.0, "B": 0.5}, n=10)
    row = pd.Series({"A": 100.0, "B": 100.0, "C": 1.0})
    with pytest.warns(UserWarning):
        w = bn.get_target_weights(prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history)
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_beta_neutral_fallback_unavailable_benchmark():
    """Returns equal-weight fallback when fetch_prices raises (no API keys, etc.)."""
    prices_history, _ = _make_beta_prices(["A"], ["B"], betas={"A": 1.0, "B": 0.5}, n=80)
    # No benchmark_prices provided → will attempt fetch and fail in test env
    bn = BetaNeutral(
        long_symbols=["A"],
        short_symbols=["B"],
        cash_symbol="C",
        benchmark_symbol="FAKESYM999",
        lookback_days=60,
    )
    row = pd.Series({"A": 100.0, "B": 100.0, "C": 1.0})
    with pytest.warns(UserWarning):
        w = bn.get_target_weights(
            prices_history.index[-1], 10_000.0, {}, row, prices_history=prices_history
        )
    assert abs(sum(w.values()) - 1.0) < 1e-9


# ── public import ─────────────────────────────────────────────────────────────

def test_beta_neutral_public_import():
    from tiportfolio import BetaNeutral as BN  # noqa: F401
    assert BN is not None
