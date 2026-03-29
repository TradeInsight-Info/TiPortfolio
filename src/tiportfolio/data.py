from __future__ import annotations

import logging
import os

import pandas as pd

from tiportfolio.helpers.data import Alpaca, YFinance

logger = logging.getLogger(__name__)


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
    """Fetch raw flat DataFrame from YFinance."""
    source = YFinance()
    return source.query(tickers, start, end)


def _query_alpaca(
    tickers: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Fetch raw flat DataFrame from Alpaca."""
    api_key = os.environ.get("ALPACA_API_KEY", "")
    api_secret = os.environ.get("ALPACA_API_SECRET", "")
    if not api_key or not api_secret:
        raise RuntimeError("ALPACA_API_KEY and ALPACA_API_SECRET must be set")
    source = Alpaca(api_key=api_key, api_secret=api_secret)
    return source.query(tickers, start, end, timeframe="1d")


def fetch_data(
    tickers: list[str],
    start: str,
    end: str,
    source: str = "yfinance",
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data. Returns dict keyed by ticker, each with UTC DatetimeIndex.

    Falls back to the other source once on failure.
    """
    primary, fallback = (
        (_query_yfinance, _query_alpaca)
        if source == "yfinance"
        else (_query_alpaca, _query_yfinance)
    )
    fallback_name = "alpaca" if source == "yfinance" else "yfinance"

    try:
        flat_df = primary(tickers, start, end)
    except Exception as e:
        logger.warning("%s failed (%s), falling back to %s", source, e, fallback_name)
        flat_df = fallback(tickers, start, end)

    return _split_flat_to_dict(flat_df)


def _split_flat_to_dict(flat_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Convert flat DataFrame with 'symbol' column to per-ticker dict."""
    result: dict[str, pd.DataFrame] = {}
    for symbol, group in flat_df.groupby("symbol"):
        df = group.drop(columns=["symbol"]).copy()
        df = df.set_index("date")
        if df.index.tz is None:
            df.index = df.index.tz_localize("US/Eastern").tz_convert("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        df.columns = [c.lower() for c in df.columns]
        result[str(symbol)] = df.sort_index()
    return result
