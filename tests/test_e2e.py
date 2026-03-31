"""End-to-end test: Quick Example from api/index.md runs without error."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import tiportfolio as ti


_DATA_DIR = Path(__file__).parent / "data"

CSV_PATHS: dict[str, str] = {
    "AAPL": str(_DATA_DIR / "aapl_2018_2024_yf.csv"),
    "QQQ": str(_DATA_DIR / "qqq_2018_2024_yf.csv"),
    "BIL": str(_DATA_DIR / "bil_2018_2024_yf.csv"),
    "GLD": str(_DATA_DIR / "gld_2018_2024_yf.csv"),
    "^VIX": str(_DATA_DIR / "vix_2018_2024_yf.csv"),
}


class TestQuickExample:
    """The Quick Example from api/index.md must work with fixture data."""

    def test_quick_example_runs(self) -> None:
        data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_PATHS)

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

    def test_weigh_based_on_beta_accessible(self) -> None:
        bench_df = pd.DataFrame(
            {"close": [100.0, 101.0, 102.0]},
            index=pd.DatetimeIndex(
                pd.bdate_range("2024-01-02", periods=3, freq="B"), tz="UTC"
            ),
        )
        algo = ti.Weigh.BasedOnBeta(
            initial_ratio={"QQQ": 0.7, "BIL": 0.3},
            target_beta=0,
            lookback=pd.DateOffset(days=5),
            base_data=bench_df,
        )
        assert algo is not None

    def test_weigh_erc_accessible(self) -> None:
        algo = ti.Weigh.ERC(lookback=pd.DateOffset(months=3))
        assert algo is not None

    def test_beta_neutral_backtest(self) -> None:
        """BasedOnBeta runs through a full backtest without error."""
        data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_PATHS)
        aapl_data = ti.fetch_data(["AAPL"], start="2019-01-01", end="2024-12-31", csv=CSV_PATHS)

        portfolio = ti.Portfolio(
            "beta_neutral_test",
            [
                ti.Signal.Monthly(),
                ti.Select.All(),
                ti.Weigh.BasedOnBeta(
                    initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1},
                    target_beta=0,
                    lookback=pd.DateOffset(months=1),
                    base_data=aapl_data["AAPL"],
                ),
                ti.Action.Rebalance(),
            ],
            ["QQQ", "BIL", "GLD"],
        )

        result = ti.run(ti.Backtest(portfolio, data))
        summary = result.summary()
        assert isinstance(summary, pd.DataFrame)
        assert "total_return" in summary.index

    def test_erc_backtest(self) -> None:
        """ERC runs through a full backtest without error."""
        data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_PATHS)

        portfolio = ti.Portfolio(
            "erc_test",
            [
                ti.Signal.Monthly(),
                ti.Select.All(),
                ti.Weigh.ERC(
                    lookback=pd.DateOffset(months=3),
                    covar_method="hist",
                ),
                ti.Action.Rebalance(),
            ],
            ["QQQ", "BIL", "GLD"],
        )

        result = ti.run(ti.Backtest(portfolio, data))
        summary = result.summary()
        assert isinstance(summary, pd.DataFrame)
        assert "total_return" in summary.index

    def test_signal_vix_accessible(self) -> None:
        vix_df = pd.DataFrame(
            {"close": [25.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-02", tz="UTC")]),
        )
        algo = ti.Signal.VIX(high=30, low=20, data={"^VIX": vix_df})
        assert algo is not None
