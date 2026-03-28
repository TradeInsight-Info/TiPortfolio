from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture()
def prices_flat() -> pd.DataFrame:
    """Raw flat DataFrame as returned by helpers — symbol column, no DatetimeIndex."""
    return pd.read_csv(DATA_DIR / "prices.csv", parse_dates=["date"])


@pytest.fixture()
def prices_dict(prices_flat: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Per-ticker dict with UTC DatetimeIndex — the format the engine expects."""
    result: dict[str, pd.DataFrame] = {}
    for symbol, group in prices_flat.groupby("symbol"):
        df = group.drop(columns=["symbol"]).copy()
        df = df.set_index("date")
        df.index = df.index.tz_localize("UTC")
        df.columns = [c.lower() for c in df.columns]
        result[str(symbol)] = df.sort_index()
    return result


@pytest.fixture()
def trading_dates(prices_dict: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Sorted union of all trading dates across tickers."""
    all_dates: set[pd.Timestamp] = set()
    for df in prices_dict.values():
        all_dates.update(df.index)
    return pd.DatetimeIndex(sorted(all_dates))
