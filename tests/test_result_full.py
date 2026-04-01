"""Tests for Chunk 5: trade recording, Trades wrapper, full_summary, charts."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import matplotlib
import numpy as np
import pandas as pd
import pytest

import tiportfolio as ti
from tiportfolio.config import TiConfig
from tiportfolio.result import BacktestResult, Trades, _SingleResult

matplotlib.use("Agg")  # no display needed

_DATA_DIR = Path(__file__).parent / "data"

CSV_PATHS: dict[str, str] = {
    "QQQ": str(_DATA_DIR / "qqq_2018_2024_yf.csv"),
    "BIL": str(_DATA_DIR / "bil_2018_2024_yf.csv"),
    "GLD": str(_DATA_DIR / "gld_2018_2024_yf.csv"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_simple_backtest() -> BacktestResult:
    """Run a simple monthly equal-weight backtest using CSV data."""
    data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2023-01-01", end="2023-12-31", csv=CSV_PATHS)
    portfolio = ti.Portfolio(
        "test_port",
        [
            ti.Signal.Monthly(),
            ti.Select.All(),
            ti.Weigh.Equally(),
            ti.Action.Rebalance(),
        ],
        ["QQQ", "BIL", "GLD"],
    )
    return ti.run(ti.Backtest(portfolio, data))


def _make_equity_curve(values: list[float]) -> pd.Series:
    dates = pd.date_range("2024-01-02", periods=len(values), freq="B", tz="UTC")
    return pd.Series(values, index=dates, name="equity")


# ---------------------------------------------------------------------------
# Trade Recording (Section 1)
# ---------------------------------------------------------------------------


class TestTradeRecording:
    def test_single_result_has_trades(self) -> None:
        result = _run_simple_backtest()
        trades = result[0].trades
        assert isinstance(trades, Trades)

    def test_trade_record_columns(self) -> None:
        result = _run_simple_backtest()
        df = result[0].trades._df
        expected_cols = {
            "date", "portfolio", "ticker", "qty_before", "qty_after",
            "delta", "price", "fee", "equity_before", "equity_after",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_trades_not_empty(self) -> None:
        result = _run_simple_backtest()
        assert len(result[0].trades) > 0

    def test_first_trade_has_zero_qty_before(self) -> None:
        result = _run_simple_backtest()
        df = result[0].trades._df
        first_trades = df[df["date"] == df["date"].min()]
        assert all(first_trades["qty_before"] == 0.0)

    def test_closed_position_has_zero_qty_after(self) -> None:
        """If a ticker is deselected, its closing trade has qty_after=0."""
        # Use momentum to force selection changes
        data = ti.fetch_data(
            ["QQQ", "BIL", "GLD"], start="2023-01-01", end="2023-12-31", csv=CSV_PATHS
        )
        portfolio = ti.Portfolio(
            "momentum_test",
            [
                ti.Signal.Monthly(),
                ti.Select.All(),
                ti.Select.Momentum(
                    n=2, lookback=pd.DateOffset(months=1), lag=pd.DateOffset(days=1)
                ),
                ti.Weigh.Equally(),
                ti.Action.Rebalance(),
            ],
            ["QQQ", "BIL", "GLD"],
        )
        result = ti.run(ti.Backtest(portfolio, data))
        df = result[0].trades._df
        # Some trades should have qty_after=0 (closed positions)
        closed = df[df["qty_after"] == 0.0]
        assert len(closed) > 0


# ---------------------------------------------------------------------------
# Trades Wrapper (Section 2)
# ---------------------------------------------------------------------------


class TestTradesWrapper:
    def test_head_delegation(self) -> None:
        result = _run_simple_backtest()
        head = result[0].trades.head(3)
        assert len(head) == 3

    def test_column_access(self) -> None:
        result = _run_simple_backtest()
        tickers = result[0].trades["ticker"]
        assert isinstance(tickers, pd.Series)

    def test_len(self) -> None:
        result = _run_simple_backtest()
        assert len(result[0].trades) > 0

    def test_sample_returns_top_and_bottom(self) -> None:
        result = _run_simple_backtest()
        sampled = result[0].trades.sample(3)
        assert isinstance(sampled, pd.DataFrame)
        # Should have up to 6 rows (3 best + 3 worst) or fewer with dedup
        assert len(sampled) <= 6

    def test_sample_with_small_n_deduplicates(self) -> None:
        result = _run_simple_backtest()
        total = len(result[0].trades)
        # Request more than half → overlap
        sampled = result[0].trades.sample(total)
        assert len(sampled) <= total


# ---------------------------------------------------------------------------
# Full Summary (Section 3)
# ---------------------------------------------------------------------------


class TestFullSummary:
    def test_full_summary_returns_dataframe(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        assert isinstance(fs, pd.DataFrame)

    def test_full_summary_includes_basic_metrics(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        metrics = fs.index.tolist()
        assert "total_return" in metrics
        assert "cagr" in metrics
        assert "sharpe" in metrics
        assert "calmar" in metrics
        assert "sortino" in metrics

    def test_sortino_positive_for_growing_equity(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        sortino = fs.loc["sortino", "value"]
        assert sortino >= 0.0

    def test_calmar_positive_for_growing_equity(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        calmar = fs.loc["calmar", "value"]
        assert calmar >= 0.0

    def test_period_return_keys_present(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        metrics = fs.index.tolist()
        for key in ["mtd", "3m", "6m", "ytd", "1y", "3y_ann", "5y_ann", "10y_ann", "incep_ann"]:
            assert key in metrics, f"Missing period return key: {key}"

    def test_period_returns_nan_for_short_data(self) -> None:
        """Short (20-day) synthetic equity → multi-year returns should be NaN."""
        values = [10000 * (1.005**i) for i in range(20)]
        eq = _make_equity_curve(values)
        from tiportfolio.config import TiConfig
        sr = _SingleResult(name="short", equity_curve=eq, config=TiConfig())
        fs = sr.full_summary()
        assert np.isnan(fs.loc["3y_ann", "value"])
        assert np.isnan(fs.loc["5y_ann", "value"])
        assert np.isnan(fs.loc["10y_ann", "value"])

    def test_daily_stats_keys_present(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        metrics = fs.index.tolist()
        for key in ["daily_mean_ann", "daily_vol_ann", "daily_skew", "daily_kurt", "best_day", "worst_day"]:
            assert key in metrics, f"Missing daily stat key: {key}"

    def test_monthly_stats_keys_present(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        metrics = fs.index.tolist()
        for key in ["monthly_sharpe", "monthly_sortino", "monthly_mean_ann", "monthly_vol_ann",
                     "monthly_skew", "monthly_kurt", "best_month", "worst_month"]:
            assert key in metrics, f"Missing monthly stat key: {key}"

    def test_yearly_stats_keys_present(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        metrics = fs.index.tolist()
        for key in ["yearly_sharpe", "yearly_sortino", "yearly_mean", "yearly_vol",
                     "yearly_skew", "yearly_kurt", "best_year", "worst_year"]:
            assert key in metrics, f"Missing yearly stat key: {key}"

    def test_drawdown_analysis_keys_present(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        metrics = fs.index.tolist()
        for key in ["avg_drawdown", "avg_drawdown_days", "avg_up_month", "avg_down_month",
                     "win_year_pct", "win_12m_pct"]:
            assert key in metrics, f"Missing drawdown analysis key: {key}"

    def test_full_summary_rounding(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        for key, val in fs["value"].items():
            if isinstance(val, float) and not np.isnan(val):
                assert val == round(val, 3), f"{key}={val} has more than 3 decimals"

    def test_avg_drawdown_monotonic_equity(self) -> None:
        """Monotonically increasing equity should have avg_drawdown of 0.0."""
        values = [10000 * (1.005**i) for i in range(252)]
        eq = _make_equity_curve(values)
        from tiportfolio.config import TiConfig
        sr = _SingleResult(name="mono", equity_curve=eq, config=TiConfig())
        fs = sr.full_summary()
        assert fs.loc["avg_drawdown", "value"] == 0.0

    def test_win_rate_metrics_bounds(self) -> None:
        result = _run_simple_backtest()
        fs = result[0].full_summary()
        assert 0.0 <= fs.loc["win_year_pct", "value"] <= 1.0
        assert 0.0 <= fs.loc["win_12m_pct", "value"] <= 1.0

    def test_backtest_result_full_summary_side_by_side(self) -> None:
        data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2023-01-01", end="2023-12-31", csv=CSV_PATHS)
        p1 = ti.Portfolio("equal", [ti.Signal.Monthly(), ti.Select.All(), ti.Weigh.Equally(), ti.Action.Rebalance()], ["QQQ", "BIL", "GLD"])
        p2 = ti.Portfolio("heavy_qqq", [ti.Signal.Monthly(), ti.Select.All(), ti.Weigh.Ratio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}), ti.Action.Rebalance()], ["QQQ", "BIL", "GLD"])
        result = ti.run(ti.Backtest(p1, data), ti.Backtest(p2, data))
        fs = result.full_summary()
        assert isinstance(fs, pd.DataFrame)
        assert "equal" in fs.columns
        assert "heavy_qqq" in fs.columns


# ---------------------------------------------------------------------------
# Chart Enhancements (Section 4)
# ---------------------------------------------------------------------------


class TestChartEnhancements:
    def test_plot_security_weights_returns_figure(self) -> None:
        result = _run_simple_backtest()
        fig = result[0].plot_security_weights()
        assert fig is not None

    def test_plot_histogram_returns_figure(self) -> None:
        result = _run_simple_backtest()
        fig = result[0].plot_histogram()
        assert fig is not None

    def test_plot_interactive_false_returns_matplotlib(self) -> None:
        result = _run_simple_backtest()
        fig = result[0].plot(interactive=False)
        assert fig is not None

    def test_plot_interactive_true_returns_plotly(self) -> None:
        result = _run_simple_backtest()
        fig = result[0].plot(interactive=True)
        # Should be a plotly Figure
        import plotly.graph_objects as go
        assert isinstance(fig, go.Figure)

    def test_backtest_result_plot_histogram(self) -> None:
        result = _run_simple_backtest()
        fig = result.plot_histogram()
        assert fig is not None

    def test_backtest_result_plot_security_weights(self) -> None:
        result = _run_simple_backtest()
        fig = result.plot_security_weights()
        assert fig is not None
