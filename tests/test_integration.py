"""Integration test: full backtest with tests/data."""

import pytest

from tiportfolio import ScheduleBasedEngine, FixRatio, Schedule


def test_integration_full_backtest(prices_three):
    """Run engine.run on full date range with QQQ/SPY/GLD; metrics finite, rebalance count sane."""
    engine = ScheduleBasedEngine(
        allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}),
        rebalance=Schedule("month_end"),
        fee_per_share=0.0035,
    )
    result = engine.run(symbols=list(prices_three.keys()), prices_df=prices_three)
    assert result.equity_curve is not None
    assert len(result.equity_curve) >= 10
    m = result.metrics
    assert m["sharpe_ratio"] == m["sharpe_ratio"]  # not nan
    assert m["cagr"] == m["cagr"]
    assert m["max_drawdown"] == m["max_drawdown"]
    assert len(result.rebalance_decisions) >= 1
    assert result.summary()


def test_integration_result_summary(prices_three):
    """BacktestResult.summary() returns a non-empty string."""
    engine = ScheduleBasedEngine(
        allocation=FixRatio(weights={"SPY": 1.0}),
        rebalance=Schedule("year_end"),
    )
    result = engine.run(
        symbols=["SPY"],
        prices_df={"SPY": prices_three["SPY"]},
        start="2019-01-01",
        end="2019-12-31",
    )
    s = result.summary()
    assert "Sharpe" in s
    assert "CAGR" in s
    assert "Rebalance" in s or "Rebalances" in s
