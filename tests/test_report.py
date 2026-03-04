"""Tests for report module: summary_table, rebalance_decisions_table, compare_strategies."""

import pandas as pd
import pytest

from tiportfolio.backtest import BacktestResult
from tiportfolio.report import compare_strategies


def test_compare_strategies_returns_dataframe_with_metrics_and_better():
    """compare_strategies returns a DataFrame with both strategy columns and 'better'."""
    equity = pd.Series([100.0, 102.0, 101.0], index=pd.DatetimeIndex(["2019-01-01", "2019-01-02", "2019-01-03"], tz="UTC"))
    metrics_a = {"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.20, "mar_ratio": 0.5, "kelly_leverage": 2.0}
    metrics_b = {"sharpe_ratio": 0.8, "cagr": 0.12, "max_drawdown": 0.25, "mar_ratio": 0.48, "kelly_leverage": 1.5}
    result_a = BacktestResult(equity_curve=equity, metrics=metrics_a, rebalance_decisions=[])
    result_b = BacktestResult(equity_curve=equity, metrics=metrics_b, rebalance_decisions=[])

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    assert list(df.columns) == ["A", "B", "better"]
    expected_index = ["sharpe_ratio", "cagr", "max_drawdown", "mar_ratio", "final_value", "kelly_leverage", "total_fee"]
    assert list(df.index) == expected_index
    assert df.loc["sharpe_ratio", "A"] == 1.0
    assert df.loc["sharpe_ratio", "B"] == 0.8
    assert df.loc["sharpe_ratio", "better"] == "A"
    assert df.loc["cagr", "better"] == "B"
    assert df.loc["max_drawdown", "better"] == "A"  # lower is better
    assert df.loc["mar_ratio", "better"] == "A"
    assert df.loc["final_value", "A"] == 101.0
    assert df.loc["final_value", "B"] == 101.0
    assert df.loc["final_value", "better"] == "tie"
    assert df.loc["kelly_leverage", "better"] == "A"
    assert df.loc["total_fee", "A"] == 0.0
    assert df.loc["total_fee", "B"] == 0.0
    assert df.loc["total_fee", "better"] == "tie"
