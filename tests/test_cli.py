from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from tiportfolio.cli import cli

DATA_DIR = str(Path(__file__).parent / "data")


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# Basic subcommands
# ---------------------------------------------------------------------------


class TestMonthly:
    def test_monthly_with_explicit_ratio(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "0.7,0.2,0.1", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        assert "sharpe" in result.output.lower()

    def test_monthly_with_day_start(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--day", "start", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0


class TestQuarterly:
    def test_quarterly_equal(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "quarterly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        assert "sharpe" in result.output.lower()

    def test_quarterly_custom_months(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "quarterly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--months", "3,6,9,12", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0


class TestWeekly:
    def test_weekly(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "weekly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0


class TestYearly:
    def test_yearly(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "yearly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0

    def test_yearly_custom_month(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "yearly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--month", "6", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0


class TestEvery:
    def test_every_5_days(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "every", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--n", "5", "--period", "day",
            "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0

    def test_every_requires_n_and_period(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "every", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code != 0


class TestOnce:
    def test_once(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "once", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Output options
# ---------------------------------------------------------------------------


class TestOutputOptions:
    def test_full_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--full", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        # full_summary has extra metrics like daily_mean
        assert "daily_mean" in result.output.lower()

    def test_leverage_single(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--leverage", "1.5", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        assert "1.5" in result.output

    def test_leverage_list(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--leverage", "1.0,1.5,2.0", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        # Should show multiple portfolio names with leverage suffixes
        assert "1.5x" in result.output
        assert "2.0x" in result.output

    def test_plot_flag(self, runner: CliRunner, tmp_path: Path) -> None:
        plot_path = tmp_path / "test_plot.png"
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--plot", str(plot_path), "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        assert plot_path.exists()


# ---------------------------------------------------------------------------
# Weigh options
# ---------------------------------------------------------------------------


class TestWeighOptions:
    def test_ratio_erc(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "erc", "--lookback", "60d", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0

    def test_ratio_hv(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "hv", "--target-hv", "0.10", "--lookback", "60d",
            "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0

    def test_ratio_hv_requires_target(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "hv", "--csv", DATA_DIR,
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Select options
# ---------------------------------------------------------------------------


class TestSelectOptions:
    def test_select_momentum(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--select", "momentum", "--top-n", "2", "--lookback", "90d",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0

    def test_select_momentum_requires_top_n(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--select", "momentum", "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_missing_tickers(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal",
        ])
        assert result.exit_code != 0

    def test_ratio_count_mismatch(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "0.7,0.2", "--csv", DATA_DIR,
        ])
        assert result.exit_code != 0
