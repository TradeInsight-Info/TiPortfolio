from __future__ import annotations

import pandas as pd

from tiportfolio.helpers.data import YFinance


def validate_data(
    data: dict[str, pd.DataFrame],
    extra: dict[str, pd.DataFrame] | None = None,
) -> None:
    """Check all DataFrames share identical DatetimeIndex. Raises ValueError if not."""
    if not data:
        return

    reference_ticker = next(iter(data))
    reference_index = data[reference_ticker].index

    all_frames = dict(data)
    if extra:
        all_frames.update(extra)

    for ticker, df in all_frames.items():
        if ticker == reference_ticker:
            continue
        if not df.index.equals(reference_index):
            raise ValueError(
                f"DatetimeIndex mismatch: '{ticker}' has {len(df.index)} dates "
                f"vs '{reference_ticker}' with {len(reference_index)} dates."
            )


def _query_yfinance(
    tickers: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Fetch raw flat DataFrame from existing YFinance helper."""
    source = YFinance()
    return source.query(tickers, start, end)


def fetch_data(
    tickers: list[str],
    start: str,
    end: str,
    source: str = "yfinance",
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data. Returns dict keyed by ticker, each with UTC DatetimeIndex."""
    flat_df = _query_yfinance(tickers, start, end)
    return _split_flat_to_dict(flat_df)


def _split_flat_to_dict(flat_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Convert flat DataFrame with 'symbol' column to per-ticker dict."""
    result: dict[str, pd.DataFrame] = {}
    for symbol, group in flat_df.groupby("symbol"):
        df = group.drop(columns=["symbol"]).copy()
        df = df.set_index("date")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        df.columns = [c.lower() for c in df.columns]
        result[str(symbol)] = df.sort_index()
    return result
