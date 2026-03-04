"""Tests for report module: summary_table, rebalance_decisions_table, compare_strategies."""

import pandas as pd

from tiportfolio.backtest import BacktestResult
from tiportfolio.report import compare_strategies

_TOP5 = ["sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown"]


def _make_result(metrics: dict) -> BacktestResult:
    equity = pd.Series(
        [100.0, 102.0, 101.0],
        index=pd.DatetimeIndex(["2019-01-01", "2019-01-02", "2019-01-03"], tz="UTC"),
    )
    return BacktestResult(equity_curve=equity, metrics=metrics, rebalance_decisions=[])


def test_compare_strategies_returns_top5_rows():
    """compare_strategies returns exactly 5 rows with the canonical top-5 index."""
    metrics_a = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    metrics_b = {"sharpe_ratio": 0.8, "sortino_ratio": 1.2, "mar_ratio": 0.48, "cagr": 0.12, "max_drawdown": 0.25}
    result_a = _make_result(metrics_a)
    result_b = _make_result(metrics_b)

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    assert list(df.index) == _TOP5
    assert len(df) == 5
    assert list(df.columns) == ["A", "B", "better"]


def test_compare_strategies_better_column():
    """compare_strategies correctly identifies the better strategy per metric."""
    metrics_a = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    metrics_b = {"sharpe_ratio": 0.8, "sortino_ratio": 1.2, "mar_ratio": 0.48, "cagr": 0.12, "max_drawdown": 0.15}
    result_a = _make_result(metrics_a)
    result_b = _make_result(metrics_b)

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    assert df.loc["sharpe_ratio", "better"] == "A"
    assert df.loc["sortino_ratio", "better"] == "A"   # higher is better
    assert df.loc["mar_ratio", "better"] == "A"
    assert df.loc["cagr", "better"] == "B"
    assert df.loc["max_drawdown", "better"] == "B"    # lower is better


def test_compare_strategies_tie():
    """compare_strategies reports 'tie' when two strategies have equal metric values."""
    metrics = {"sharpe_ratio": 1.0, "sortino_ratio": 1.5, "mar_ratio": 0.5, "cagr": 0.10, "max_drawdown": 0.20}
    result_a = _make_result(metrics)
    result_b = _make_result(metrics)

    df = compare_strategies(result_a, result_b, names=["A", "B"])

    for metric in _TOP5:
        assert df.loc[metric, "better"] == "tie"
