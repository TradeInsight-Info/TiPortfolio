from __future__ import annotations

import logging
import os
from pathlib import Path

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
    csv: str | dict[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data. Returns dict keyed by ticker, each with UTC DatetimeIndex.

    Args:
        tickers: List of ticker symbols.
        start: Start date string (e.g. "2019-01-01").
        end: End date string (e.g. "2024-12-31").
        source: Data source — "yfinance" or "alpaca".
        csv: Optional CSV source for offline loading. Either:
            - A directory path (str) — auto-discovers ``<ticker>.csv`` files
              (case-insensitive lookup).
            - A dict mapping ticker to CSV file path.
            Each CSV must have a ``date`` index and ``open,high,low,close,volume`` columns.

    Falls back to the other source once on failure.
    """
    if csv is not None:
        return _load_from_csv(tickers, csv)

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


def _load_from_csv(
    tickers: list[str],
    csv: str | dict[str, str],
) -> dict[str, pd.DataFrame]:
    """Load per-ticker CSV files into the standard dict format.

    Args:
        tickers: List of ticker symbols to load.
        csv: Directory path (auto-discover) or dict of {ticker: filepath}.
    """
    if isinstance(csv, dict):
        # Validate all tickers have entries before loading any files
        missing = sorted(set(tickers) - set(csv.keys()))
        if missing:
            raise FileNotFoundError(
                f"CSV paths missing for tickers: {', '.join(missing)}. "
                f"Provided keys: {', '.join(sorted(csv.keys()))}"
            )
        paths = csv
    else:
        csv_dir = Path(csv)
        paths: dict[str, str] = {}
        missing_tickers: list[str] = []
        for ticker in tickers:
            candidates = [
                csv_dir / f"{ticker}.csv",
                csv_dir / f"{ticker.lower()}.csv",
                csv_dir / f"{ticker.upper()}.csv",
            ]
            found = next((p for p in candidates if p.exists()), None)
            if found is None:
                missing_tickers.append(ticker)
            else:
                paths[ticker] = str(found)
        if missing_tickers:
            raise FileNotFoundError(
                f"CSV files not found for tickers: {', '.join(missing_tickers)} "
                f"in {csv_dir}"
            )

    result: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        filepath = paths[ticker]
        df = pd.read_csv(filepath, index_col="date", parse_dates=True)
        result[ticker] = _normalize_ticker_df(df, default_tz="UTC", ticker=ticker)
    return result


def _normalize_ticker_df(
    df: pd.DataFrame, default_tz: str = "UTC", ticker: str = "",
) -> pd.DataFrame:
    """Lowercase columns, convert index to UTC, sort, drop all-NaN rows."""
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is None:
        df.index = df.index.tz_localize(default_tz).tz_convert("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df = df.sort_index()
    nan_mask = df.isna().all(axis=1)
    if nan_mask.any():
        nan_dates = df.index[nan_mask]
        logger.warning(
            "%s: dropped %d all-NaN rows from %s to %s",
            ticker or "unknown", len(nan_dates), nan_dates[0].date(), nan_dates[-1].date(),
        )
        df = df.loc[~nan_mask]
    return df


def _split_flat_to_dict(flat_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Convert flat DataFrame with 'symbol' column to per-ticker dict."""
    result: dict[str, pd.DataFrame] = {}
    for symbol, group in flat_df.groupby("symbol"):
        df = group.drop(columns=["symbol"]).copy()
        df = df.set_index("date")
        result[str(symbol)] = _normalize_ticker_df(df, default_tz="US/Eastern", ticker=str(symbol))
    return result
