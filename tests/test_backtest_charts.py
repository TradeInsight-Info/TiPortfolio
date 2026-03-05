"""Unit tests for BacktestResult chart methods: plot_portfolio_beta and plot_rolling_book_composition."""

import numpy as np
import pandas as pd
import pytest

from tiportfolio.backtest import BacktestResult, RebalanceDecision


@pytest.fixture
def sample_equity_curve():
    """Create a sample equity curve."""
    dates = pd.date_range("2023-01-01", periods=252, freq="D", tz="UTC")
    values = 10000 * (1 + np.cumsum(np.random.randn(252) * 0.01))
    return pd.Series(values, index=dates, name="equity")


@pytest.fixture
def sample_asset_curves():
    """Create sample asset curves for multiple assets."""
    np.random.seed(42)  # Reproducible
    dates = pd.date_range("2023-01-01", periods=252, freq="D", tz="UTC")
    data = {
        "AAPL": 150 * (1 + np.cumsum(np.random.randn(252) * 0.008)),
        "GOOGL": 100 * (1 + np.cumsum(np.random.randn(252) * 0.010)),
        "MSFT": 300 * (1 + np.cumsum(np.random.randn(252) * 0.009)),
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sample_benchmark_prices(sample_asset_curves):
    """Create sample benchmark prices matching asset_curves dates."""
    # Use same dates as asset_curves for alignment
    values = 400 * (1 + np.cumsum(np.random.randn(len(sample_asset_curves)) * 0.007))
    df = pd.DataFrame({"SPY": values}, index=sample_asset_curves.index)
    return df


@pytest.fixture
def sample_result(sample_equity_curve, sample_asset_curves):
    """Create a sample BacktestResult."""
    return BacktestResult(
        equity_curve=sample_equity_curve,
        metrics={
            "sharpe_ratio": 1.5,
            "sortino_ratio": 2.0,
            "cagr": 0.15,
            "max_drawdown": 0.10,
        },
        rebalance_decisions=[],
        asset_curves=sample_asset_curves,
        total_fee=0.0,
    )


# === Tests for plot_portfolio_beta() ===

class TestPlotPortfolioBeta:
    """Test suite for plot_portfolio_beta() method."""

    def test_plot_portfolio_beta_with_provided_prices(self, sample_result, sample_benchmark_prices):
        """User provides benchmark_prices as DataFrame."""
        # Ensure benchmark has enough data and matches asset_curves index exactly
        benchmark = pd.DataFrame(
            {"SPY": sample_benchmark_prices["SPY"].values},
            index=sample_result.asset_curves.index,
        )

        fig = sample_result.plot_portfolio_beta(
            benchmark_symbol="SPY",
            benchmark_prices=benchmark,
            lookback_days=30,
        )
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].name == "Portfolio Beta"

    def test_plot_portfolio_beta_tz_naive_asset_curves(self, sample_equity_curve, sample_asset_curves):
        """Asset curves are tz-naive; benchmark is tz-aware."""
        # Create tz-naive asset curves
        naive_asset_curves = sample_asset_curves.copy()
        naive_asset_curves.index = naive_asset_curves.index.tz_localize(None)

        result = BacktestResult(
            equity_curve=sample_equity_curve,
            metrics={"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.10},
            asset_curves=naive_asset_curves,
        )

        # Create tz-aware benchmark matching the indices
        tz_aware_index = naive_asset_curves.index.tz_localize("UTC")
        benchmark = pd.DataFrame({
            "SPY": 400 * (1 + np.cumsum(np.random.randn(252) * 0.007))
        }, index=tz_aware_index)

        # Should handle mixed timezones gracefully
        fig = result.plot_portfolio_beta(benchmark_prices=benchmark, lookback_days=30)
        assert fig is not None

    def test_plot_portfolio_beta_mixed_tz_awareness(self, sample_equity_curve):
        """Test mixed timezone awareness (one tz-aware, one tz-naive)."""
        # tz-aware asset curves
        dates_aware = pd.date_range("2023-01-01", periods=252, freq="D", tz="UTC")
        asset_curves = pd.DataFrame(
            {"AAPL": 150 * (1 + np.random.randn(252).cumsum() * 0.008)},
            index=dates_aware,
        )

        # tz-naive benchmark
        dates_naive = pd.date_range("2023-01-01", periods=252, freq="D")
        benchmark = pd.DataFrame(
            {"SPY": 400 * (1 + np.random.randn(252).cumsum() * 0.007)},
            index=dates_naive,
        )

        result = BacktestResult(
            equity_curve=sample_equity_curve,
            metrics={"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.10},
            asset_curves=asset_curves,
        )

        fig = result.plot_portfolio_beta(benchmark_prices=benchmark, lookback_days=30)
        assert fig is not None

    def test_plot_portfolio_beta_insufficient_dates(self, sample_result, sample_benchmark_prices):
        """Raises ValueError when insufficient overlapping dates."""
        short_benchmark = sample_benchmark_prices.head(50)  # Only 50 dates

        with pytest.raises(ValueError, match="Not enough overlapping dates"):
            sample_result.plot_portfolio_beta(
                benchmark_prices=short_benchmark,
                lookback_days=60,  # Need at least 61 dates
            )

    def test_plot_portfolio_beta_chart_formatting(self, sample_result, sample_benchmark_prices):
        """Chart includes reference lines and proper formatting."""
        # Ensure benchmark matches asset_curves index
        benchmark = pd.DataFrame(
            {"SPY": sample_benchmark_prices["SPY"].values},
            index=sample_result.asset_curves.index,
        )

        fig = sample_result.plot_portfolio_beta(
            benchmark_prices=benchmark,
            lookback_days=30,
        )

        # Check title
        assert "lookback=30" in fig.layout.title.text

        # Check reference lines (hlines add shapes)
        assert len(fig.layout.shapes) >= 2  # Should have at least β=0 and β=1 lines

        # Check hover template
        assert "Beta" in fig.data[0].hovertemplate

    def test_plot_portfolio_beta_alpaca_style_timestamps(self, sample_equity_curve):
        """Alpaca returns timestamps with 05:00:00+00:00 (midnight Eastern in UTC).

        After tz_localize(None), these become 05:00:00 which does NOT match
        YFinance's midnight dates (00:00:00). The fix must normalize to midnight.
        """
        np.random.seed(42)
        # Simulate Alpaca-style index: market open time = 05:00 UTC (= midnight Eastern)
        business_days = pd.bdate_range("2023-01-01", periods=252)
        alpaca_index = pd.DatetimeIndex(
            [d + pd.Timedelta(hours=5) for d in business_days], tz="UTC"
        )
        asset_curves = pd.DataFrame(
            {"AAPL": 150 * (1 + np.cumsum(np.random.randn(252) * 0.008))},
            index=alpaca_index,
        )
        equity_curve = pd.Series(
            10000 * (1 + np.cumsum(np.random.randn(252) * 0.01)),
            index=alpaca_index,
        )
        result = BacktestResult(
            equity_curve=equity_curve,
            metrics={"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.10},
            asset_curves=asset_curves,
        )

        # Benchmark uses midnight tz-naive dates (YFinance-style)
        yf_index = pd.DatetimeIndex(business_days)
        benchmark = pd.DataFrame(
            {"SPY": 400 * (1 + np.cumsum(np.random.randn(252) * 0.007))},
            index=yf_index,
        )

        # Without the fix this raises: "Not enough overlapping dates. Need at least 61, got 0"
        fig = result.plot_portfolio_beta(benchmark_prices=benchmark, lookback_days=60)
        assert fig is not None
        assert len(fig.data) > 0

    def test_plot_portfolio_beta_zero_benchmark_variance(self, sample_equity_curve, sample_asset_curves):
        """Handles edge case where benchmark has zero variance."""
        # Create benchmark with constant value (zero variance)
        benchmark = pd.DataFrame(
            {"SPY": np.ones(len(sample_asset_curves)) * 400},
            index=sample_asset_curves.index,
        )

        result = BacktestResult(
            equity_curve=sample_equity_curve,
            metrics={"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.10},
            asset_curves=sample_asset_curves,
        )

        fig = result.plot_portfolio_beta(benchmark_prices=benchmark, lookback_days=30)
        # Should return figure even with zero variance (will have NaNs)
        assert fig is not None
        assert np.isnan(np.array(fig.data[0].y)).any()  # Beta values should include NaNs


# === Tests for plot_rolling_book_composition() ===

class TestPlotRollingBookComposition:
    """Test suite for plot_rolling_book_composition() method."""

    def test_plot_rolling_book_composition_missing_column(self, sample_result):
        """Raises KeyError when column doesn't exist."""
        with pytest.raises(KeyError, match="nonexistent_column"):
            sample_result.plot_rolling_book_composition("nonexistent_column")

    def test_plot_rolling_book_composition_no_asset_curves(self, sample_equity_curve):
        """Raises ValueError when asset_curves is None."""
        result = BacktestResult(
            equity_curve=sample_equity_curve,
            metrics={"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.10},
            asset_curves=None,
        )

        with pytest.raises(ValueError, match="asset_curves is not available"):
            result.plot_rolling_book_composition("nonexistent")

    def test_plot_rolling_book_composition_structure_note(self):
        """Note: plot_rolling_book_composition expects book_column to contain nested position data.

        The method iterates over (asset, value) pairs in each row, treating the column values
        as Series or dict-like objects. This is used for long/short book visualization where
        the asset_curves contains structured position data, not simple price series.

        For full testing, we would need either:
        1. A properly structured asset_curves with nested Series/dicts per cell
        2. Or a refactoring of the method to work with standard DataFrames

        Current tests focus on error handling and method existence.
        """
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
