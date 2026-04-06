"""Tests for CLI --aip flag."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from tiportfolio.cli import cli

DATA_DIR = str(Path(__file__).parent / "data")


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestCLIAIPMonthly:
    """2.1 — monthly --aip produces output with contribution metrics."""

    def test_aip_output_contains_contributions(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR, "--aip", "1000",
        ])
        assert result.exit_code == 0, result.output
        assert "total_contributions" in result.output
        assert "contribution_count" in result.output


class TestCLINoAIP:
    """2.2 — without --aip, no contribution metrics in output."""

    def test_no_aip_no_contributions(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
        ])
        assert result.exit_code == 0
        assert "total_contributions" not in result.output


class TestCLIAIPWithLeverage:
    """2.3 — --aip works with --leverage."""

    def test_aip_with_leverage(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, [
            "monthly", "--tickers", "QQQ,BIL,GLD",
            "--start", "2019-01-01", "--end", "2024-12-31",
            "--ratio", "equal", "--csv", DATA_DIR,
            "--aip", "1000", "--leverage", "1.5",
        ])
        assert result.exit_code == 0, result.output
        assert "total_contributions" in result.output


class TestCLIAIPHelp:
    """2.4 — --aip appears in --help output."""

    def test_aip_in_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["monthly", "--help"])
        assert result.exit_code == 0
        assert "--aip" in result.output
