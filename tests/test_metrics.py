"""Tests for performance metrics."""

import pandas as pd
import pytest

from tiportfolio.metrics import compute_metrics

CANONICAL_KEYS = ["sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown", "kelly_leverage", "mean_excess_return"]


def test_metrics_trivial_series():
    """Metrics on a trivial equity series are finite and in expected range."""
    equity = pd.Series(
        [1.0, 1.01, 0.99, 1.02],
        index=pd.date_range("2020-01-01", periods=4, freq="D"),
    )
    m = compute_metrics(equity)
    assert "sharpe_ratio" in m
    assert "sortino_ratio" in m
    assert "cagr" in m
    assert "max_drawdown" in m
    assert "mar_ratio" in m
    assert "mean_excess_return" in m
    assert 0 <= m["max_drawdown"] <= 1
    assert m["cagr"] > -1  # not a total loss


def test_metrics_canonical_key_order():
    """compute_metrics returns keys in canonical order."""
    equity = pd.Series(
        [100.0, 101.0, 100.5, 102.0, 101.5],
        index=pd.date_range("2020-01-01", periods=5, freq="D"),
    )
    m = compute_metrics(equity)
    assert list(m.keys()) == CANONICAL_KEYS


def test_metrics_empty_series_all_nan():
    """compute_metrics returns all nan for empty series."""
    m = compute_metrics(pd.Series(dtype=float))
    assert list(m.keys()) == CANONICAL_KEYS
    for v in m.values():
        assert pd.isna(v)


def test_metrics_sortino_nan_when_no_downside():
    """sortino_ratio is nan when there are no down days."""
    equity = pd.Series(
        [100.0, 101.0, 102.0, 103.0, 104.0],
        index=pd.date_range("2020-01-01", periods=5, freq="D"),
    )
    m = compute_metrics(equity, risk_free_rate=0.0)
    assert pd.isna(m["sortino_ratio"])


def test_metrics_sortino_finite_with_mixed_returns():
    """sortino_ratio is finite when there are both up and down days."""
    equity = pd.Series(
        [100.0, 102.0, 99.0, 103.0, 101.0, 105.0],
        index=pd.date_range("2020-01-01", periods=6, freq="D"),
    )
    m = compute_metrics(equity)
    assert pd.notna(m["sortino_ratio"])
    assert isinstance(m["sortino_ratio"], float)


def test_metrics_mean_excess_return_positive():
    """mean_excess_return is positive for a rising series above risk-free rate."""
    equity = pd.Series(
        [100.0] + [100.0 * (1.001 ** i) for i in range(1, 30)],
        index=pd.date_range("2020-01-01", periods=30, freq="D"),
    )
    m = compute_metrics(equity, risk_free_rate=0.01)  # low rf, so excess should be positive
    assert pd.notna(m["mean_excess_return"])
    assert m["mean_excess_return"] > 0


def test_metrics_aapl_data():
    """Test compute_metrics on AAPL data from 2018-2024 returns accurate results with all attributes."""
    df = pd.read_csv("tests/data/aapl.csv")
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = df.set_index('date')
    df = df.loc['2018':'2024']
    equity = df['close']

    result = compute_metrics(equity, risk_free_rate=0.04)

    assert list(result.keys()) == CANONICAL_KEYS

    # All values should be finite
    for key in result:
        assert pd.notna(result[key]), f"{key} should not be NaN"
        assert isinstance(result[key], (int, float)), f"{key} should be a number"

    # Existing metric values unchanged
    assert result["sharpe_ratio"] == pytest.approx(1.7317463314573784, rel=1e-9)
    assert result["cagr"] == pytest.approx(0.866174638867431, rel=1e-9)
    assert result["max_drawdown"] == pytest.approx(0.3142532221379833, rel=1e-9)
    assert result["mar_ratio"] == pytest.approx(2.756295171691536, rel=1e-9)
    assert result["kelly_leverage"] == pytest.approx(4.57535190062222, rel=1e-9)

    # New metrics: exact values
    assert result["sortino_ratio"] == pytest.approx(2.2062826094371797, rel=1e-9)
    assert result["mean_excess_return"] == pytest.approx(0.6554567652180477, rel=1e-9)
