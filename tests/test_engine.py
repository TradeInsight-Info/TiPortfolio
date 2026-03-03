"""Tests for backtest engine."""

import pandas as pd
import pytest

from tiportfolio import (
    BacktestEngine,
    FixRatio,
    Schedule,
    ScheduleBasedEngine,
    VixRegimeAllocation,
    VolatilityBasedEngine,
)
from tiportfolio.data import load_csvs


def test_engine_run_returns_result(prices_three):
    """engine.run(prices=dict) returns BacktestResult with equity_curve and metrics."""
    engine = BacktestEngine(
        allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}),
        rebalance=Schedule("month_end"),
        fee_per_share=0,
    )
    result = engine.run(prices=prices_three, start="2019-01-01", end="2019-06-30")
    assert result.equity_curve is not None
    assert len(result.equity_curve) >= 1
    assert "sharpe_ratio" in result.metrics
    assert "cagr" in result.metrics
    assert "max_drawdown" in result.metrics
    assert "mar_ratio" in result.metrics


def test_engine_rebalance_count_matches_calendar(prices_three):
    """Number of rebalance decisions matches schedule in date range."""
    prices_two = {k: prices_three[k] for k in ("SPY", "QQQ")}
    engine = BacktestEngine(
        allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.5}),
        rebalance=Schedule("quarter_end"),
        fee_per_share=0.0035,
    )
    result = engine.run(prices=prices_two, start="2019-01-01", end="2019-12-31")
    # 4 quarters in 2019 -> expect 4 rebalances
    assert 3 <= len(result.rebalance_decisions) <= 5
    for d in result.rebalance_decisions:
        assert d.equity_before >= 0
        assert d.equity_after >= 0
        assert d.fee_paid >= 0


def test_engine_rejects_prices_keys_mismatch(prices_three):
    """run() raises when prices keys don't match allocation."""
    engine = BacktestEngine(
        allocation=FixRatio(weights={"SPY": 0.5, "MISSING": 0.5}),
        rebalance=Schedule("month_end"),
    )
    with pytest.raises(ValueError, match="prices"):
        engine.run(prices=prices_three)


def test_engine_single_asset_empty_rebalance_decisions(prices_three):
    """Single-asset (buy-and-hold) produces no rebalance decisions."""
    prices_spy = {"SPY": prices_three["SPY"]}
    engine = BacktestEngine(
        allocation=FixRatio(weights={"SPY": 1.0}),
        rebalance=Schedule("month_start"),
        fee_per_share=0.0035,
    )
    result = engine.run(prices=prices_spy, start="2019-01-01", end="2019-12-31")
    assert len(result.rebalance_decisions) == 0
    assert result.equity_curve is not None
    assert len(result.equity_curve) >= 1
    assert not pd.isna(result.metrics["sharpe_ratio"])


def test_schedule_based_engine_uses_prices_df(prices_three):
    """ScheduleBasedEngine with prices_df uses the dict and does not fetch."""
    allocation = FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2})
    schedule = Schedule("month_end")
    start, end = "2019-01-01", "2019-06-30"
    engine_base = BacktestEngine(
        allocation=allocation,
        rebalance=schedule,
        fee_per_share=0,
    )
    result_ref = engine_base.run(prices=prices_three, start=start, end=end)
    engine_fetcher = ScheduleBasedEngine(
        allocation=allocation,
        rebalance=schedule,
        fee_per_share=0,
    )
    result = engine_fetcher.run(
        symbols=["SPY", "QQQ", "GLD"],
        start=start,
        end=end,
        prices_df=prices_three,
    )
    assert result.equity_curve is not None
    assert len(result.equity_curve) == len(result_ref.equity_curve)
    pd.testing.assert_series_equal(result.equity_curve, result_ref.equity_curve)
    assert result.metrics["sharpe_ratio"] == pytest.approx(result_ref.metrics["sharpe_ratio"])


def test_volatility_based_engine_uses_prices_df():
    """VolatilityBasedEngine with prices_df uses the dict and does not fetch."""
    ix = pd.date_range("2019-01-02", periods=10, freq="B")
    n = len(ix)
    prices = {
        "SPY": pd.DataFrame({"close": [280.0 + i * 0.1 for i in range(n)]}, index=ix),
        "QQQ": pd.DataFrame({"close": [180.0 + i * 0.1 for i in range(n)]}, index=ix),
        "GLD": pd.DataFrame({"close": [120.0 + i * 0.1 for i in range(n)]}, index=ix),
        "VIX": pd.DataFrame(
            {"close": [25.0] * 5 + [32.0] * 5},
            index=ix,
        ),
    }
    allocation = VixRegimeAllocation(
        high_vol_allocation=FixRatio(weights={"SPY": 0.33, "QQQ": 0.33, "GLD": 0.34}),
        low_vol_allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}),
    )
    engine_base = VolatilityBasedEngine(
        allocation=allocation,
        rebalance=Schedule("vix_regime"),
        fee_per_share=0,
    )
    result_ref = engine_base.run(
        symbols=["SPY", "QQQ", "GLD"],
        start=ix[0],
        end=ix[-1],
        prices_df=prices,
        volatility_symbol="VIX",
        target_vix=20.0,
        lower_bound=-1.0,
        upper_bound=10.0,
    )
    engine_fetcher = VolatilityBasedEngine(
        allocation=allocation,
        rebalance=Schedule("vix_regime"),
        fee_per_share=0,
    )
    result = engine_fetcher.run(
        symbols=["SPY", "QQQ", "GLD"],
        start=ix[0],
        end=ix[-1],
        prices_df=prices,
        volatility_symbol="VIX",
        target_vix=20.0,
        lower_bound=-1.0,
        upper_bound=10.0,
    )
    assert result.equity_curve is not None
    assert len(result.equity_curve) == len(result_ref.equity_curve)
    pd.testing.assert_series_equal(result.equity_curve, result_ref.equity_curve)
    assert len(result.rebalance_decisions) == len(result_ref.rebalance_decisions)
