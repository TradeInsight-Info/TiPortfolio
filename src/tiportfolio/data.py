from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from tiportfolio.helpers.data import Alpaca, TiData, YFinance

logger = logging.getLogger(__name__)


def validate_data(
    data: dict[str, pd.DataFrame],
    extra: dict[str, pd.DataFrame] | None = None,
) -> None:
    """Check all DataFrames share identical DatetimeIndex.

    Args:
        data: Dict mapping ticker symbols to OHLCV DataFrames.
        extra: Optional additional DataFrames to validate (e.g., VIX data).

    Raises:
        ValueError: If any DataFrame has a different DatetimeIndex.
    """
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


def _query_tidata(
    tickers: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Fetch raw flat DataFrame from the TradeInsight Trading Data Service."""
    api_key = os.environ.get("TRADEINSIGHT_API_KEY", "")
    if not api_key:
        raise RuntimeError("TRADEINSIGHT_API_KEY must be set")
    source = TiData(api_key=api_key)
    return source.query(tickers, start, end)


def _tidata_available() -> bool:
    """True when a TradeInsight API key is configured."""
    return bool(os.environ.get("TRADEINSIGHT_API_KEY"))


def _alpaca_available() -> bool:
    """True when both Alpaca credentials are configured."""
    return bool(
        os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_API_SECRET")
    )


# Data providers in priority order: (name, is_available). yfinance has no
# availability gate — it is the always-reachable floor. The query function for
# each is `_query_<name>`, resolved from module globals at call time so tests
# can patch it.
_PROVIDERS: list[tuple[str, Callable[[], bool]]] = [
    ("tidata", _tidata_available),
    ("alpaca", _alpaca_available),
    ("yfinance", lambda: True),
]


def _query_fn(name: str) -> Callable[..., pd.DataFrame]:
    return globals()[f"_query_{name}"]


def fetch_data(
    tickers: list[str],
    start: str,
    end: str,
    source: str = "auto",
    csv: str | dict[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data. Returns dict keyed by ticker, each with UTC DatetimeIndex.

    Args:
        tickers: List of ticker symbols.
        start: Start date string (e.g. "2019-01-01").
        end: End date string (e.g. "2024-12-31").
        source: Data source. ``"auto"`` (default) selects by available
            credentials in priority order — ``tidata`` (``TRADEINSIGHT_API_KEY``),
            then ``alpaca`` (``ALPACA_API_KEY``/``ALPACA_API_SECRET``), then
            ``yfinance`` — falling through to the next provider on failure.
            Pass ``"tidata"``, ``"alpaca"``, or ``"yfinance"`` to force one.
        csv: Optional CSV source for offline loading. Either:
            - A directory path (str) — auto-discovers ``<ticker>.csv`` files
              (case-insensitive lookup).
            - A dict mapping ticker to CSV file path.
            Each CSV must have a ``date`` index and ``open,high,low,close,volume`` columns.

    Raises:
        ValueError: If ``source`` is not "auto" or a known provider name.
    """
    if csv is not None:
        return _load_from_csv(tickers, csv)

    if source == "auto":
        names = [name for name, avail in _PROVIDERS if avail()]
    else:
        names = [name for name, _ in _PROVIDERS if name == source]
        if not names:
            raise ValueError(
                f"Unknown source: {source!r}. Use 'auto', 'tidata', "
                f"'alpaca', or 'yfinance'."
            )

    last_exc: Exception | None = None
    for name in names:
        try:
            return _split_flat_to_dict(_query_fn(name)(tickers, start, end))
        except Exception as e:
            logger.warning("data source %s failed (%s), trying next", name, e)
            last_exc = e

    # Every candidate errored ('auto' always has the yfinance floor, so this is
    # reached only when all providers failed; an explicit source re-raises its
    # own error).
    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"No data source available for source={source!r}")


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


def _align_indices(data: dict[str, pd.DataFrame]) -> None:
    """Restrict all tickers to their common (intersection) dates, in place.

    Providers that fetch per symbol (e.g. tidata) can return different date
    coverage per ticker, and the engine requires a shared DatetimeIndex. Align
    to the intersection so downstream ``validate_data`` passes and no NaN prices
    leak into the simulation. A no-op when every ticker already shares the same
    dates; drops (with a warning) only the non-overlapping dates otherwise.
    """
    if len(data) < 2:
        return
    indices = [df.index for df in data.values()]
    common = indices[0]
    for idx in indices[1:]:
        common = common.intersection(idx)
    for ticker, df in data.items():
        if len(df) != len(common):
            logger.warning(
                "%s: dropped %d date(s) not shared by all tickers",
                ticker, len(df) - len(common),
            )
            data[ticker] = df.loc[common]


def _split_flat_to_dict(flat_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Convert flat DataFrame with 'symbol' column to per-ticker dict."""
    result: dict[str, pd.DataFrame] = {}
    for symbol, group in flat_df.groupby("symbol"):
        df = group.drop(columns=["symbol"]).copy()
        df = df.set_index("date")
        result[str(symbol)] = _normalize_ticker_df(df, default_tz="US/Eastern", ticker=str(symbol))
    _align_indices(result)
    return result
