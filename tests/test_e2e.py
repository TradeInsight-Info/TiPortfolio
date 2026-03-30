"""End-to-end test: Quick Example from api/index.md runs without error."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import tiportfolio as ti


class TestQuickExample:
    """The Quick Example from api/index.md must work with fixture data."""

    def test_quick_example_runs(self, prices_dict: dict[str, pd.DataFrame], prices_flat: pd.DataFrame) -> None:
        # Mock fetch_data to return our fixture instead of hitting network
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")

        portfolio = ti.Portfolio(
            "monthly_rebalance",
            [
                ti.Signal.Monthly(),
                ti.Select.All(),
                ti.Weigh.Equally(),
                ti.Action.Rebalance(),
            ],
            ["QQQ", "BIL", "GLD"],
        )

        result = ti.run(ti.Backtest(portfolio, data))

        # Verify it produces usable output
        summary = result.summary()
        assert isinstance(summary, pd.DataFrame)
        assert "total_return" in summary.index
        assert "sharpe" in summary.index

        # plot() should return a figure (not crash)
        import matplotlib
        matplotlib.use("Agg")  # no display needed
        fig = result.plot()
        assert fig is not None

    def test_public_api_imports(self) -> None:
        """All expected symbols are importable from tiportfolio."""
        assert hasattr(ti, "fetch_data")
        assert hasattr(ti, "validate_data")
        assert hasattr(ti, "run")
        assert hasattr(ti, "Backtest")
        assert hasattr(ti, "Portfolio")
        assert hasattr(ti, "TiConfig")
        assert hasattr(ti, "Signal")
        assert hasattr(ti, "Select")
        assert hasattr(ti, "Weigh")
        assert hasattr(ti, "Action")
        # Chunk 2: branching combinators
        assert hasattr(ti, "Or")
        assert hasattr(ti, "And")
        assert hasattr(ti, "Not")

    def test_signal_weekly_accessible(self) -> None:
        algo = ti.Signal.Weekly()
        assert algo is not None

    def test_signal_yearly_accessible(self) -> None:
        algo = ti.Signal.Yearly()
        assert algo is not None

    def test_signal_every_n_periods_accessible(self) -> None:
        algo = ti.Signal.EveryNPeriods(n=2, period="week")
        assert algo is not None

    def test_signal_monthly_accessible(self) -> None:
        algo = ti.Signal.Monthly()
        assert algo is not None

    def test_select_all_accessible(self) -> None:
        algo = ti.Select.All()
        assert algo is not None

    def test_weigh_equally_accessible(self) -> None:
        algo = ti.Weigh.Equally()
        assert algo is not None

    def test_action_rebalance_accessible(self) -> None:
        algo = ti.Action.Rebalance()
        assert algo is not None

    def test_signal_vix_accessible(self) -> None:
        vix_df = pd.DataFrame(
            {"close": [25.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-02", tz="UTC")]),
        )
        algo = ti.Signal.VIX(high=30, low=20, data={"^VIX": vix_df})
        assert algo is not None
