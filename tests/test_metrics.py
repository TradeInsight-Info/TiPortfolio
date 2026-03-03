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


def test_metrics_aapl_data():
    """Test compute_metrics on AAPL data from 2018-2024 returns accurate results with all attributes."""
    import pandas as pd

    df = pd.read_csv("tests/data/aapl.csv")
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = df.set_index('date')
    df = df.loc['2018':'2024']  # Filter to 2018-2024 range
    equity = df['close']

    result = compute_metrics(equity, risk_free_rate=0.04)

    # Assert all expected attributes are present
    expected_keys = {"sharpe_ratio", "cagr", "max_drawdown", "mar_ratio", "kelly_leverage"}
    assert set(result.keys()) == expected_keys

    # Assert all values are finite (accurate computation)
    for key in expected_keys:
        assert pd.notna(result[key]), f"{key} should not be NaN"
        assert isinstance(result[key], (int, float)), f"{key} should be a number"

    # Assert accurate values
    assert result["sharpe_ratio"] == pytest.approx(1.7317463314573784, rel=1e-9)
    assert result["cagr"] == pytest.approx(0.866174638867431, rel=1e-9)
    assert result["max_drawdown"] == pytest.approx(0.3142532221379833, rel=1e-9)
    assert result["mar_ratio"] == pytest.approx(2.756295171691536, rel=1e-9)
    assert result["kelly_leverage"] == pytest.approx(4.57535190062222, rel=1e-9)
