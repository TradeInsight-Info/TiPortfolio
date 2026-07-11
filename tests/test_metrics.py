"""Pure-metrics tests: exercise tiportfolio.metrics through a synthetic
equity curve, with no backtest run required."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tiportfolio import metrics
from tiportfolio.config import TiConfig


def _curve(values: list[float]) -> pd.Series:
    idx = pd.date_range("2020-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(values, index=idx, name="equity")


def test_return_stats_flat_curve_has_zero_return_and_drawdown() -> None:
    eq = _curve([10_000.0] * 252)
    stats = metrics.return_stats(eq, TiConfig())
    assert stats["total_return"] == 0.0
    assert stats["max_drawdown"] == 0.0
    assert stats["final_value"] == 10_000.0


def test_return_stats_monotonic_growth_is_positive_no_drawdown() -> None:
    eq = _curve([10_000 * (1.001**i) for i in range(252)])
    stats = metrics.return_stats(eq, TiConfig())
    assert stats["total_return"] > 0.0
    assert stats["cagr"] > 0.0
    assert stats["max_drawdown"] == 0.0
    assert stats["sharpe"] > 0.0


def test_drawdown_analysis_zero_for_monotonic_equity() -> None:
    eq = _curve([10_000 * (1.005**i) for i in range(252)])
    dd = metrics.drawdown_analysis(eq, TiConfig())
    assert dd["avg_drawdown"] == 0.0
    assert 0.0 <= dd["win_year_pct"] <= 1.0


def test_period_returns_nan_beyond_available_history() -> None:
    eq = _curve([10_000 * (1.005**i) for i in range(20)])
    pr = metrics.period_returns(eq, TiConfig())
    assert np.isnan(pr["3y_ann"])
    assert np.isnan(pr["10y_ann"])
