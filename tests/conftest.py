"""Pytest fixtures for TiPortfolio tests."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import pytest


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
    prices = load_csvs(paths)
    # Convert single price column to OHLC format
    for symbol, df in prices.items():
        price_series = df[symbol]
        df['open'] = price_series
        df['high'] = price_series
        df['low'] = price_series
        df['close'] = price_series
        del df[symbol]
    return prices


def load_csvs(
    paths: Iterable[str | Path],
) -> dict[str, pd.DataFrame]:
    """Load multiple CSVs into a dict symbol -> DataFrame.

    Each path can be a file path; symbol is inferred from the 'symbol' column
    in the CSV, or from the stem of the filename (e.g. spy.csv -> SPY if symbol
    column missing). Returns raw DataFrames without any data transformation.
    """
    result: dict[str, pd.DataFrame] = {}
    for path in paths:
        path = Path(path)
        if path.suffix.lower() != ".csv":
            continue
        df = pd.read_csv(path)
        if "symbol" in df.columns:
            sym = str(df["symbol"].iloc[0])
        else:
            sym = path.stem.upper()
        result[sym] = df
    return result
