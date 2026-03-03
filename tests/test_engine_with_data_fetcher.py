"""Tests for ScheduleBasedEngine (symbol-based data fetch)."""

from unittest.mock import patch

import pytest

from tiportfolio import FixRatio, Schedule, ScheduleBasedEngine


def test_schedule_based_engine_run_returns_result(prices_three):
    """ScheduleBasedEngine.run(symbols=...) returns BacktestResult when fetch succeeds."""
    with patch("tiportfolio.engine.fetch_prices", return_value=prices_three):
        engine = ScheduleBasedEngine(
            allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}),
            rebalance=Schedule("month_end"),
            fee_per_share=0,
        )
        result = engine.run(
            symbols=["SPY", "QQQ", "GLD"],
            start="2019-01-01",
            end="2019-06-30",
        )
    assert result.equity_curve is not None
    assert len(result.equity_curve) >= 1
    assert "sharpe_ratio" in result.metrics
    assert "cagr" in result.metrics
    assert "max_drawdown" in result.metrics


def test_schedule_based_engine_requires_start_end():
    """run(symbols=...) raises when start or end is missing."""
    engine = ScheduleBasedEngine(
        allocation=FixRatio(weights={"SPY": 1.0}),
        rebalance=Schedule("month_end"),
    )
    with pytest.raises(ValueError, match="start and end are required"):
        engine.run(symbols=["SPY"], start=None, end="2024-12-31")
    with pytest.raises(ValueError, match="start and end are required"):
        engine.run(symbols=["SPY"], start="2019-01-01", end=None)


def test_schedule_based_engine_raises_on_fetch_failure():
    """When fetch fails, run() raises RuntimeError with message containing 'Failed to fetch data'."""
    with patch(
        "tiportfolio.engine.fetch_prices",
        side_effect=RuntimeError("Failed to fetch data: connection refused"),
    ):
        engine = ScheduleBasedEngine(
            allocation=FixRatio(weights={"SPY": 1.0}),
            rebalance=Schedule("month_end"),
        )
        with pytest.raises(RuntimeError, match="Failed to fetch data"):
            engine.run(symbols=["SPY"], start="2019-01-01", end="2019-12-31")
