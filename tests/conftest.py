"""Pytest fixtures for TiPortfolio tests."""

from pathlib import Path

import pytest

from tiportfolio.data import load_csvs


@pytest.fixture
def data_dir() -> Path:
    """Path to tests/data directory."""
    return Path(__file__).resolve().parent / "data"


@pytest.fixture
def prices_dict(data_dir: Path) -> dict:
    """Load all CSVs from tests/data into dict symbol -> DataFrame."""
    paths = list(data_dir.glob("*.csv"))
    return load_csvs(paths)


@pytest.fixture
def prices_three(data_dir: Path) -> dict:
    """Dict with SPY, QQQ, GLD for integration tests."""
    paths = [data_dir / "spy.csv", data_dir / "qqq.csv", data_dir / "gld.csv"]
    return load_csvs(paths)
