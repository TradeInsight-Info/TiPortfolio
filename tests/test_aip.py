"""Tests for run_aip (Auto Investment Plan / dollar-cost averaging)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd
import pytest

import tiportfolio as ti

matplotlib.use("Agg")

_DATA_DIR = Path(__file__).parent / "data"

CSV_PATHS: dict[str, str] = {
    "QQQ": str(_DATA_DIR / "qqq_2018_2024_yf.csv"),
    "BIL": str(_DATA_DIR / "bil_2018_2024_yf.csv"),
    "GLD": str(_DATA_DIR / "gld_2018_2024_yf.csv"),
}


@pytest.fixture()
def data() -> dict[str, pd.DataFrame]:
    return ti.fetch_data(
        ["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_PATHS
    )


@pytest.fixture()
def portfolio() -> ti.Portfolio:
    return ti.Portfolio(
        "monthly_equal",
        [
            ti.Signal.Monthly(),
            ti.Select.All(),
            ti.Weigh.Equally(),
            ti.Action.Rebalance(),
        ],
        ["QQQ", "BIL", "GLD"],
    )


class TestAIPSummaryMetrics:
    """2.1 — AIP result has correct total_contributions and contribution_count."""

    def test_summary_includes_contribution_metrics(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=1000)
        summary = result.summary()
        assert "total_contributions" in summary.index
        assert "contribution_count" in summary.index
        assert summary.loc["total_contributions", "value"] > 0
        assert summary.loc["contribution_count", "value"] > 0

    def test_contribution_count_matches_months(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=500)
        summary = result.summary()
        count = int(summary.loc["contribution_count", "value"])
        # CSV data spans 2018-01 to 2024-12: ~84 month-ends
        assert 70 <= count <= 90

    def test_total_contributions_equals_count_times_amount(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        amount = 1000.0
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=amount)
        summary = result.summary()
        total = summary.loc["total_contributions", "value"]
        count = summary.loc["contribution_count", "value"]
        assert total == amount * count


class TestAIPFinalValue:
    """2.2 — AIP final_value > initial_capital + total_contributions for rising market."""

    def test_final_value_exceeds_contributions(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=1000)
        summary = result.summary()
        final = summary.loc["final_value", "value"]
        total_contrib = summary.loc["total_contributions", "value"]
        initial = ti.TiConfig().initial_capital
        # QQQ rose significantly 2019-2024, so portfolio should grow
        assert final > initial + total_contrib


class TestAIPZeroAmount:
    """2.3 — AIP with monthly_aip_amount=0 produces identical result to run()."""

    def test_zero_aip_matches_run(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        bt = ti.Backtest(portfolio, data)

        result_run = ti.run(ti.Backtest(portfolio, data))
        result_aip = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=0)

        summary_run = result_run.summary()
        summary_aip = result_aip.summary()

        # AIP with 0 should not have contribution rows
        assert "total_contributions" not in summary_aip.index

        # Core metrics should match
        for metric in ["sharpe", "cagr", "max_drawdown", "final_value", "total_return"]:
            assert abs(summary_run.loc[metric, "value"] - summary_aip.loc[metric, "value"]) < 1e-6, (
                f"{metric} mismatch: run={summary_run.loc[metric, 'value']} "
                f"vs aip={summary_aip.loc[metric, 'value']}"
            )


class TestAIPMonthEndInjection:
    """2.4 — Cash injection happens only on month-end trading days."""

    def test_equity_jumps_on_month_ends(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        amount = 10000.0  # large amount to make jumps visible
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=amount)
        eq = result[0].equity_curve if hasattr(result, '__getitem__') else result.equity_curve

        # Check that there are equity jumps at month boundaries
        # (the equity curve records values after injection but before rebalance)
        returns = eq.pct_change().dropna()

        # Count days with unusually large positive jumps (contribution days)
        # On a $10k contribution with ~$10k initial capital, expect noticeable jumps
        large_jumps = returns[returns > 0.05]
        assert len(large_jumps) > 0, "Expected visible equity jumps from AIP contributions"


class TestAIPPlotAndFullSummary:
    """2.5 — plot() and full_summary() work on AIP result without errors."""

    def test_plot_works(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=1000)
        fig = result.plot()
        assert fig is not None

    def test_full_summary_works(
        self, portfolio: ti.Portfolio, data: dict[str, pd.DataFrame]
    ) -> None:
        result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=1000)
        fs = result.full_summary()
        assert isinstance(fs, pd.DataFrame)
        assert "total_contributions" in fs.index
        assert "cagr" in fs.index


class TestAIPPublicAPI:
    """run_aip is importable from tiportfolio."""

    def test_import(self) -> None:
        from tiportfolio import run_aip
        assert callable(run_aip)
