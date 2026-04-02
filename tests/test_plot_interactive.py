"""Tests for plot_interactive() and _per_asset_equity()."""

from __future__ import annotations

import pandas as pd
import pytest

from tiportfolio.config import TiConfig
from tiportfolio.result import BacktestResult, _SingleResult


def _make_prices() -> dict[str, pd.DataFrame]:
    """Create minimal price DataFrames for 2 tickers."""
    dates = pd.date_range("2024-01-02", periods=20, freq="B", tz="UTC")
    qqq = pd.DataFrame({"close": [400 + i * 2 for i in range(20)]}, index=dates)
    bil = pd.DataFrame({"close": [91.0] * 20}, index=dates)
    return {"QQQ": qqq, "BIL": bil}


def _make_trade_records(dates: pd.DatetimeIndex) -> list[dict[str, object]]:
    """Create minimal trade records with buys and sells."""
    return [
        # Initial buy on day 0
        {"date": dates[0], "portfolio": "test", "ticker": "QQQ",
         "qty_before": 0.0, "qty_after": 17.5, "delta": 17.5,
         "price": 400.0, "fee": 0.06, "equity_before": 10000, "equity_after": 10000},
        {"date": dates[0], "portfolio": "test", "ticker": "BIL",
         "qty_before": 0.0, "qty_after": 22.0, "delta": 22.0,
         "price": 91.0, "fee": 0.08, "equity_before": 10000, "equity_after": 10000},
        # Rebalance on day 10: sell some QQQ, buy more BIL
        {"date": dates[10], "portfolio": "test", "ticker": "QQQ",
         "qty_before": 17.5, "qty_after": 15.0, "delta": -2.5,
         "price": 420.0, "fee": 0.01, "equity_before": 10500, "equity_after": 10500},
        {"date": dates[10], "portfolio": "test", "ticker": "BIL",
         "qty_before": 22.0, "qty_after": 33.0, "delta": 11.0,
         "price": 91.0, "fee": 0.04, "equity_before": 10500, "equity_after": 10500},
    ]


def _make_result_with_prices() -> _SingleResult:
    prices = _make_prices()
    dates = pd.date_range("2024-01-02", periods=20, freq="B", tz="UTC")
    values = [10000 + i * 50 for i in range(20)]
    equity = pd.Series(values, index=dates, name="equity")
    records = _make_trade_records(dates)
    return _SingleResult(
        name="test", equity_curve=equity, config=TiConfig(),
        trade_records=records, prices=prices,
    )


class TestPerAssetEquity:
    def test_shape_and_columns(self) -> None:
        sr = _make_result_with_prices()
        df = sr._per_asset_equity()
        assert df.shape[0] == 20
        assert "QQQ" in df.columns
        assert "BIL" in df.columns
        assert "total" in df.columns

    def test_total_matches_equity_curve(self) -> None:
        sr = _make_result_with_prices()
        df = sr._per_asset_equity()
        pd.testing.assert_series_equal(df["total"], sr.equity_curve, check_names=False)

    def test_forward_fills_positions(self) -> None:
        sr = _make_result_with_prices()
        df = sr._per_asset_equity()
        # Day 5 should have the same QQQ qty as day 0 (17.5 * price)
        day5_qqq = df["QQQ"].iloc[5]
        expected_price = 400 + 5 * 2  # 410
        assert abs(day5_qqq - 17.5 * expected_price) < 1.0

    def test_empty_records(self) -> None:
        dates = pd.date_range("2024-01-02", periods=5, freq="B", tz="UTC")
        equity = pd.Series([10000] * 5, index=dates)
        sr = _SingleResult(name="empty", equity_curve=equity, config=TiConfig())
        df = sr._per_asset_equity()
        assert "total" in df.columns
        assert df.shape[0] == 5


class TestPlotInteractiveSingle:
    def test_returns_plotly_figure(self) -> None:
        import plotly.graph_objects as go
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        assert isinstance(fig, go.Figure)

    def test_has_asset_traces(self) -> None:
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        trace_names = [t.name for t in fig.data]
        assert "QQQ" in trace_names
        assert "BIL" in trace_names
        assert "Total" in trace_names

    def test_has_buy_sell_markers(self) -> None:
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        trace_names = [t.name for t in fig.data]
        assert "Buy" in trace_names
        assert "Sell" in trace_names

    def test_buy_markers_are_green_triangles(self) -> None:
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        buy_trace = next(t for t in fig.data if t.name == "Buy")
        assert buy_trace.marker.symbol == "triangle-up"
        assert buy_trace.marker.color == "green"

    def test_sell_markers_are_red_triangles(self) -> None:
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        sell_trace = next(t for t in fig.data if t.name == "Sell")
        assert sell_trace.marker.symbol == "triangle-down"
        assert sell_trace.marker.color == "red"

    def test_has_drawdown_subplot(self) -> None:
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        drawdown_trace = next(t for t in fig.data if t.name == "Drawdown")
        assert drawdown_trace.fill == "tozeroy"

    def test_buy_markers_on_asset_lines(self) -> None:
        """Buy markers should be positioned at the asset's value, not total."""
        sr = _make_result_with_prices()
        fig = sr.plot_interactive()
        buy_trace = next(t for t in fig.data if t.name == "Buy")
        asset_eq = sr._per_asset_equity()
        # First buy is QQQ at day 0
        expected_y = float(asset_eq["QQQ"].iloc[0])
        assert abs(buy_trace.y[0] - expected_y) < 1.0


class TestPlotInteractiveMulti:
    def _make_multi(self) -> BacktestResult:
        r1 = _make_result_with_prices()
        prices = _make_prices()
        dates = pd.date_range("2024-01-02", periods=20, freq="B", tz="UTC")
        equity2 = pd.Series([10000 + i * 30 for i in range(20)], index=dates)
        r2 = _SingleResult(
            name="baseline", equity_curve=equity2, config=TiConfig(),
            trade_records=[{
                "date": dates[0], "portfolio": "baseline", "ticker": "QQQ",
                "qty_before": 0.0, "qty_after": 25.0, "delta": 25.0,
                "price": 400.0, "fee": 0.09, "equity_before": 10000, "equity_after": 10000,
            }],
            prices=prices,
        )
        return BacktestResult([r1, r2])

    def test_returns_plotly_figure(self) -> None:
        import plotly.graph_objects as go
        result = self._make_multi()
        fig = result.plot_interactive()
        assert isinstance(fig, go.Figure)

    def test_has_one_equity_trace_per_strategy(self) -> None:
        result = self._make_multi()
        fig = result.plot_interactive()
        line_traces = [t for t in fig.data if t.mode == "lines"]
        names = [t.name for t in line_traces]
        assert "test" in names
        assert "baseline" in names

    def test_has_trade_markers(self) -> None:
        result = self._make_multi()
        fig = result.plot_interactive()
        marker_traces = [t for t in fig.data if t.mode == "markers"]
        assert len(marker_traces) >= 2  # at least buy + sell for "test", buy for "baseline"

    def test_single_delegates(self) -> None:
        import plotly.graph_objects as go
        r = _make_result_with_prices()
        result = BacktestResult([r])
        fig = result.plot_interactive()
        assert isinstance(fig, go.Figure)
        # Single should show per-asset traces
        trace_names = [t.name for t in fig.data]
        assert "QQQ" in trace_names

    def test_has_drawdown_traces(self) -> None:
        result = self._make_multi()
        fig = result.plot_interactive()
        # Each strategy should have a DD trace in row 2
        dd_traces = [t for t in fig.data if "DD" in (t.name or "")]
        assert len(dd_traces) == 2
