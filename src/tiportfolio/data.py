"""Data loading and normalization for TiPortfolio backtests.

Accepts a dict of DataFrames (symbol -> df with date index and price column).
Validates keys match allocation and converts to a single merged DataFrame.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from tiportfolio.helpers.data import Alpaca, YFinance
from tiportfolio.utils.constants import VOLATILITY_INDEX_SYMBOLS

if TYPE_CHECKING:
    from collections.abc import Iterable


DEFAULT_PRICE_COLUMN = "close"


def load_csv(
    path: str | Path,
    *,
    symbol: str | None = None,
    date_column: str = "date",
    price_column: str = DEFAULT_PRICE_COLUMN,
) -> pd.DataFrame:
    """Load a single CSV into a DataFrame with datetime index and price column.

    Expects CSV with columns including `date_column` and `price_column`.
    If `symbol` is None and CSV has a 'symbol' column, the first value is used.
    """
    path = Path(path)
    df = pd.read_csv(path)
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column], utc=True)
        df = df.set_index(date_column)
    if symbol is None and "symbol" in df.columns:
        symbol = str(df["symbol"].iloc[0])
    if price_column not in df.columns:
        raise ValueError(f"CSV missing price column {price_column!r}: {path}")
    out = df[[price_column]].copy()
    out.index.name = "date"
    if symbol is not None:
        out.columns = [symbol]
    return out


def load_csvs(
    paths: Iterable[str | Path],
    *,
    date_column: str = "date",
    price_column: str = DEFAULT_PRICE_COLUMN,
) -> dict[str, pd.DataFrame]:
    """Load multiple CSVs into a dict symbol -> DataFrame.

    Each path can be a file path; symbol is inferred from the 'symbol' column
    in the CSV, or from the stem of the filename (e.g. spy.csv -> SPY if symbol
    column missing). Each DataFrame has a datetime index and one price column.
    """
    result: dict[str, pd.DataFrame] = {}
    for path in paths:
        path = Path(path)
        if path.suffix.lower() != ".csv":
            continue
        df = pd.read_csv(path)
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column], utc=True)
            df = df.set_index(date_column)
        if "symbol" in df.columns:
            sym = str(df["symbol"].iloc[0])
        else:
            sym = path.stem.upper()
        if price_column not in df.columns:
            raise ValueError(f"CSV missing price column {price_column!r}: {path}")
        frame = df[[price_column]].copy()
        frame.index.name = "date"
        frame.columns = [sym]
        result[sym] = frame
    return result


def validate_prices_keys(
    prices: dict[str, pd.DataFrame],
    allocation_keys: set[str],
) -> None:
    """Raise ValueError if prices keys do not match allocation keys."""
    price_keys = set(prices.keys())
    if price_keys != allocation_keys:
        missing = allocation_keys - price_keys
        extra = price_keys - allocation_keys
        msg_parts = []
        if missing:
            msg_parts.append(f"prices missing keys for allocation: {sorted(missing)}")
        if extra:
            msg_parts.append(f"prices have extra keys not in allocation: {sorted(extra)}")
        raise ValueError("; ".join(msg_parts))


def merge_prices(
    prices: dict[str, pd.DataFrame],
    *,
    price_column: str = DEFAULT_PRICE_COLUMN,
    how: str = "inner",
) -> pd.DataFrame:
    """Convert dict of DataFrames to a single DataFrame (date index, one column per symbol).

    Each value can be a DataFrame with datetime index and one column (or a column
    named `price_column`). Result has a common date index and one column per symbol.
    """
    if not prices:
        return pd.DataFrame()

    series_list: list[pd.Series] = []
    for symbol, df in prices.items():
        if df.index.name is None and "date" in df.columns:
            df = df.set_index("date")
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.copy()
            df.index = pd.to_datetime(df.index, utc=True)
        if price_column in df.columns:
            ser = df[price_column].rename(symbol)
        elif len(df.columns) == 1:
            ser = df.iloc[:, 0].rename(symbol)
        else:
            raise ValueError(
                f"DataFrame for {symbol!r} must have one price column or column {price_column!r}"
            )
        series_list.append(ser)

    merged = pd.concat(series_list, axis=1, join=how)
    merged.index.name = "date"
    return merged.sort_index()


def normalize_prices(
    prices: dict[str, pd.DataFrame],
    allocation_keys: set[str],
    *,
    price_column: str = DEFAULT_PRICE_COLUMN,
    how: str = "inner",
) -> pd.DataFrame:
    """Validate prices keys match allocation and return merged DataFrame."""
    validate_prices_keys(prices, allocation_keys)
    return merge_prices(prices, price_column=price_column, how=how)


def fetch_prices(
    symbols: Iterable[str],
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
) -> dict[str, pd.DataFrame]:
    """Fetch price data by symbols from Alpaca (if API keys set) or Yahoo Finance.

    Internal use only. Not exported. Raises RuntimeError with message
    'Failed to fetch data: ...' if both sources fail.
    """

    sym_list = [s.upper() if isinstance(s, str) else str(s).upper() for s in symbols]
    if not sym_list:
        raise RuntimeError("Failed to fetch data: no symbols provided")
    requested = set(sym_list)
    cause: str | None = None

    # Try Alpaca if credentials are set
    api_key = os.environ.get("ALPACA_API_KEY", "").strip()
    api_secret = os.environ.get("ALPACA_API_SECRET", "").strip()
    if api_key and api_secret:
        try:
            alpaca = Alpaca(api_key=api_key, api_secret=api_secret)
            df = alpaca.query(
                sym_list,
                start_date=start,
                end_date=end,
                timeframe="1d",
                adjust="all",
            )
            if df is not None and not df.empty:
                result = prices_dict_from_long_format(df)
                missing = requested - set(result.keys())
                if not missing:
                    return result
                cause = f"missing symbols: {sorted(missing)}"
        except Exception as e:
            cause = str(e)

    # Fallback to YFinance
    try:
        yf = YFinance(auto_adjust=True)
        df = yf.query(sym_list, start_date=start, end_date=end)
        if df is not None and not df.empty:
            result = prices_dict_from_long_format(df)
            missing = requested - set(result.keys())
            if not missing:
                return result
            cause = cause or f"missing symbols: {sorted(missing)}"
        else:
            cause = cause or "no data returned"
    except Exception as e:
        cause = cause or str(e)

    raise RuntimeError(f"Failed to fetch data: {cause}")


def fetch_volatility_index(
    symbol: str,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
) -> pd.DataFrame:
    """Fetch a single volatility index (VIX, VVIX, RVX, VXD) via YFinance (Yahoo Finance).

    symbol: One of VIX, VVIX, RVX, VXD (case-insensitive; ^ prefix allowed).
    Returns a DataFrame with datetime index and a "close" column.
    Raises ValueError if symbol is not allowed; raises RuntimeError on fetch failure.
    """
    s = symbol.strip().upper().lstrip("^")
    if s not in VOLATILITY_INDEX_SYMBOLS:
        raise ValueError(
            f"volatility index symbol must be one of {VOLATILITY_INDEX_SYMBOLS}; got {symbol!r}"
        )
    # Yahoo Finance uses ^ prefix for indices (e.g. ^VIX, ^VVIX)
    ticker = f"^{s}"
    yf = YFinance(auto_adjust=True)
    df = yf.query([ticker], start_date=start, end_date=end)
    if df is None or df.empty:
        raise RuntimeError(f"Failed to fetch data: no data returned for {symbol!r}")
    result = prices_dict_from_long_format(df)
    if not result:
        raise RuntimeError(f"Failed to fetch data: no data returned for {symbol!r}")
    out = next(iter(result.values()))
    # Ensure "close" column name for engine compatibility
    if "close" not in out.columns and len(out.columns) == 1:
        out = out.rename(columns={out.columns[0]: "close"})
    return out


def prices_dict_from_long_format(
    df: pd.DataFrame,
    *,
    date_column: str = "date",
    symbol_column: str = "symbol",
    price_column: str = DEFAULT_PRICE_COLUMN,
) -> dict[str, pd.DataFrame]:
    """Convert a long-format DataFrame (symbol, date, close) to dict symbol -> DataFrame.

    Compatible with output from tiportfolio.helpers.data.YFinance or Alpaca:
    columns must include date_column, symbol_column, and price_column.
    Each value is a DataFrame with datetime index (UTC) and one price column.
    """
    for col in (date_column, symbol_column, price_column):
        if col not in df.columns:
            raise ValueError(f"DataFrame missing column {col!r}")
    result: dict[str, pd.DataFrame] = {}
    for sym in df[symbol_column].unique():
        sub = (
            df.loc[df[symbol_column] == sym, [date_column, price_column]]
            .set_index(date_column)
            .sort_index()
        )
        sub.index = pd.to_datetime(sub.index, utc=True)
        sub.columns = [sym]
        sub.index.name = "date"
        result[str(sym)] = sub
    return result
