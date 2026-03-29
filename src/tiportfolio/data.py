from __future__ import annotations

import itertools
import os

import pandas as pd
import yfinance


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


def _make_session() -> object | None:
    """Create a curl_cffi session with verify=False if TI_SSL_NOVERIFY is set."""
    if os.environ.get("TI_SSL_NOVERIFY", "").strip() in ("1", "true", "yes"):
        try:
            from curl_cffi.requests import Session
            session = Session()
            session.verify = False
            return session
        except ImportError:
            return None
    return None


def _query_yfinance(
    tickers: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Fetch raw flat DataFrame via yfinance.download."""
    session = _make_session()
    df = yfinance.download(
        tickers,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        session=session,
    )
    if df.empty:
        raise ValueError(f"No data returned for tickers: {tickers}")

    df = df.reset_index()
    symbols = tickers if len(tickers) > 1 else tickers

    result = pd.DataFrame()
    if len(tickers) == 1:
        sym = tickers[0]
        result["date"] = df["Date"].values
        result["symbol"] = list(itertools.repeat(sym, len(df)))
        result["open"] = df["Open"].values
        result["high"] = df["High"].values
        result["low"] = df["Low"].values
        result["close"] = df["Close"].values
        result["volume"] = df["Volume"].values
    else:
        df.columns = df.columns.to_flat_index()
        for sym in symbols:
            sym_df = pd.DataFrame()
            sym_df["date"] = df[("Date", "")].values
            sym_df["symbol"] = list(itertools.repeat(sym, len(df[("Close", sym)].values)))
            sym_df["open"] = df[("Open", sym)].values
            sym_df["high"] = df[("High", sym)].values
            sym_df["low"] = df[("Low", sym)].values
            sym_df["close"] = df[("Close", sym)].values
            sym_df["volume"] = df[("Volume", sym)].values
            result = pd.concat((result, sym_df))

    return result


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
