"""Tests for performance metrics."""

import pandas as pd
import pytest

from tiportfolio.metrics import compute_metrics


def test_metrics_trivial_series():
    """Metrics on a trivial equity series are finite and in expected range."""
    equity = pd.Series(
        [1.0, 1.01, 0.99, 1.02],
        index=pd.date_range("2020-01-01", periods=4, freq="D"),
    )
    m = compute_metrics(equity)
    assert "sharpe_ratio" in m
    assert "cagr" in m
    assert "max_drawdown" in m
    assert "mar_ratio" in m
    assert 0 <= m["max_drawdown"] <= 1
    assert m["cagr"] > -1  # not a total loss


def test_metrics_empty_series():
    """Empty series returns nan metrics."""
    m = compute_metrics(pd.Series(dtype=float))
    assert pd.isna(m["sharpe_ratio"])
    assert pd.isna(m["cagr"])
    assert pd.isna(m["max_drawdown"])
    assert pd.isna(m["mar_ratio"])
