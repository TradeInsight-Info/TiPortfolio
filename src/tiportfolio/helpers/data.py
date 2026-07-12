r"""Contains :class:`.DataSource`\ s used to fetch external OHLCV data.

Derived from pybroker's data sources (Copyright (C) 2023 Edward West,
https://github.com/edtechre/pybroker, Apache 2.0 with Commons Clause) but
reduced to a self-contained, cache-free implementation: the query pipeline
here validates inputs, fetches, verifies columns, and returns a flat
DataFrame — nothing more.
"""

from __future__ import annotations

import itertools
import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Final, Iterable, Optional, Union

import alpaca.data.historical.crypto as alpaca_crypto
import alpaca.data.historical.stock as alpaca_stock
import numpy as np
import pandas as pd
import yfinance
from alpaca.data.enums import Adjustment
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from tidata.tifinance import Ticker


class DataCol(Enum):
    """Default data column names."""

    DATE = "date"
    SYMBOL = "symbol"
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"
    VWAP = "vwap"


_REQUIRED_COLS: Final = (
    DataCol.SYMBOL,
    DataCol.DATE,
    DataCol.OPEN,
    DataCol.HIGH,
    DataCol.LOW,
    DataCol.CLOSE,
)


def _to_datetime(
    date: Union[str, datetime, np.datetime64, pd.Timestamp],
) -> datetime:
    """Convert ``date`` to a plain :class:`datetime`."""
    if isinstance(date, pd.Timestamp):
        return date.to_pydatetime()  # type: ignore[union-attr]
    if isinstance(date, datetime):
        return date
    if isinstance(date, str):
        return pd.to_datetime(date).to_pydatetime()
    if isinstance(date, np.datetime64):
        return pd.Timestamp(date).to_pydatetime()
    raise TypeError(f"Unsupported date type: {type(date)}")


def _verify_date_range(start_date: datetime, end_date: datetime) -> None:
    if start_date > end_date:
        raise ValueError(
            f"start_date ({start_date}) must be on or before end_date "
            f"({end_date})."
        )


def _verify_columns(df: pd.DataFrame) -> None:
    missing = [c.value for c in _REQUIRED_COLS if c.value not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing!r}")


class DataSource(ABC):
    """Base class for querying OHLCV data from an external source.

    Extend and override :meth:`._fetch_data` to add a custom source. The
    returned :class:`pandas.DataFrame` must contain the columns ``symbol``,
    ``date``, ``open``, ``high``, ``low``, and ``close``.
    """

    def query(
        self,
        symbols: Union[str, Iterable[str]],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: Optional[str] = "",
        adjust: Optional[Any] = None,
    ) -> pd.DataFrame:
        """Query data and return it as a flat :class:`pandas.DataFrame`.

        Args:
            symbols: Symbols of the data to query.
            start_date: Start date of the data to query (inclusive).
            end_date: End date of the data to query (inclusive).
            timeframe: Source-specific timeframe string (e.g. ``"1d"``).
            adjust: The type of adjustment to make.

        Returns:
            :class:`pandas.DataFrame` sorted by date then symbol.
        """
        start = _to_datetime(start_date)
        end = _to_datetime(end_date)
        _verify_date_range(start, end)
        if isinstance(symbols, str) and not symbols:
            raise ValueError("Symbols cannot be empty.")
        unique_syms = (
            frozenset((symbols,))
            if isinstance(symbols, str)
            else frozenset(symbols)
        )
        if not unique_syms:
            raise ValueError("Symbols cannot be empty.")
        df = self._fetch_data(unique_syms, start, end, timeframe, adjust)
        _verify_columns(df)
        if not df.empty:
            df = df.sort_values(by=[DataCol.DATE.value, DataCol.SYMBOL.value])
        return df.reset_index(drop=True)

    @abstractmethod
    def _fetch_data(
        self,
        symbols: frozenset[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: Optional[str],
        adjust: Optional[Any],
    ) -> pd.DataFrame:
        """Fetch raw data for ``symbols``. See class docstring for the
        required output columns."""


_TF_PATTERN: Final = re.compile(r"(\d+)([A-Za-z]+)")
_TF_ABBR: Final = {
    "s": "sec",
    "m": "min",
    "h": "hour",
    "d": "day",
    "w": "week",
}


def parse_timeframe(timeframe: str) -> list[tuple[int, str]]:
    """Parse a timeframe string into ``(amount, unit)`` parts.

    Units accept both short and long forms: ``s``/``sec``, ``m``/``min``,
    ``h``/``hour``, ``d``/``day``, ``w``/``week``. Example: ``"1h 30m"``.
    """
    parts = _TF_PATTERN.findall(timeframe)
    if not parts or len(parts) != len(timeframe.split()):
        raise ValueError("Invalid timeframe format.")
    result = []
    units = frozenset(_TF_ABBR.values())
    seen_units = set()
    for part in parts:
        unit = part[1].lower()
        if unit in _TF_ABBR:
            unit = _TF_ABBR[unit]
        if unit not in units:
            raise ValueError("Invalid timeframe format.")
        if unit in seen_units:
            raise ValueError("Invalid timeframe format.")
        result.append((int(part[0]), unit))
        seen_units.add(unit)
    return result


def _parse_alpaca_timeframe(
    timeframe: Optional[str],
) -> tuple[int, TimeFrameUnit]:
    if timeframe is None:
        raise ValueError("Timeframe needs to be specified for Alpaca.")
    parts = parse_timeframe(timeframe)
    if len(parts) != 1:
        raise ValueError(f"Invalid Alpaca timeframe: {timeframe}")
    amount, unit = parts[0]
    if unit == "min":
        return amount, TimeFrameUnit.Minute
    if unit == "hour":
        return amount, TimeFrameUnit.Hour
    if unit == "day":
        return amount, TimeFrameUnit.Day
    if unit == "week":
        return amount, TimeFrameUnit.Week
    raise ValueError(f"Invalid Alpaca timeframe: {timeframe}")


class Alpaca(DataSource):
    """Retrieves stock data from `Alpaca <https://alpaca.markets/>`_."""

    __EST: Final = "US/Eastern"

    def __init__(self, api_key: str, api_secret: str):
        self._api = alpaca_stock.StockHistoricalDataClient(api_key, api_secret)

    def query(
        self,
        symbols: Union[str, Iterable[str]],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: Optional[str] = "1d",
        adjust: Optional[Any] = "all",
    ) -> pd.DataFrame:
        _parse_alpaca_timeframe(timeframe)
        return super().query(symbols, start_date, end_date, timeframe, adjust)

    def _fetch_data(
        self,
        symbols: frozenset[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: Optional[str],
        adjust: Optional[Any],
    ) -> pd.DataFrame:
        amount, unit = _parse_alpaca_timeframe(timeframe)
        adj_enum = None
        if adjust is not None:
            for member in Adjustment:
                if member.value == adjust:
                    adj_enum = member
                    break
            if adj_enum is None:
                raise ValueError(f"Unknown adjustment: {adjust}.")
        request = StockBarsRequest(
            symbol_or_symbols=list(symbols),
            start=start_date,
            end=end_date,
            timeframe=TimeFrame(amount, unit),
            limit=None,
            adjustment=adj_enum,
            feed=None,
        )
        df = self._api.get_stock_bars(request).df  # type: ignore[union-attr]
        if df.columns.empty:
            return pd.DataFrame(columns=[col.value for col in DataCol])
        if df.empty:
            return df
        df = df.reset_index()
        df.rename(columns={"timestamp": DataCol.DATE.value}, inplace=True)
        df = df[[col.value for col in DataCol]]
        df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
        df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(
            self.__EST
        )
        return df


class AlpacaCrypto(DataSource):
    """Retrieves crypto data from `Alpaca <https://alpaca.markets/>`_.

    Args:
        api_key: Alpaca API key.
        api_secret: Alpaca API secret.
    """

    TRADE_COUNT: Final = "trade_count"
    COLUMNS: Final = (
        DataCol.SYMBOL.value,
        DataCol.DATE.value,
        DataCol.OPEN.value,
        DataCol.HIGH.value,
        DataCol.LOW.value,
        DataCol.CLOSE.value,
        DataCol.VOLUME.value,
        DataCol.VWAP.value,
        TRADE_COUNT,
    )

    __EST: Final = "US/Eastern"

    def __init__(self, api_key: str, api_secret: str):
        self._api = alpaca_crypto.CryptoHistoricalDataClient(
            api_key, api_secret
        )

    def query(
        self,
        symbols: Union[str, Iterable[str]],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: Optional[str] = "1d",
        _adjust: Optional[str] = None,
    ) -> pd.DataFrame:
        _parse_alpaca_timeframe(timeframe)
        return super().query(symbols, start_date, end_date, timeframe, _adjust)

    def _fetch_data(
        self,
        symbols: frozenset[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: Optional[str],
        _adjust: Optional[str],
    ) -> pd.DataFrame:
        amount, unit = _parse_alpaca_timeframe(timeframe)
        request = CryptoBarsRequest(
            symbol_or_symbols=list(symbols),
            start=start_date,
            end=end_date,
            timeframe=TimeFrame(amount, unit),
            limit=None,
        )
        df = self._api.get_crypto_bars(request).df  # type: ignore[union-attr]
        if df.columns.empty:
            return pd.DataFrame(columns=self.COLUMNS)
        if df.empty:
            return df
        df = df.reset_index()
        df.rename(columns={"timestamp": DataCol.DATE.value}, inplace=True)
        df = df[[col for col in self.COLUMNS]]
        df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
        df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(
            self.__EST
        )
        return df


class YFinance(DataSource):
    r"""Retrieves data from `Yahoo Finance <https://finance.yahoo.com/>`_\ .

    Args:
        auto_adjust: Whether to auto adjust close prices. If ``True``, then
            adjusted close prices are stored in the ``close`` column. Defaults
            to ``True``.

    Attributes:
        ADJ_CLOSE: Column name of adjusted close prices.
    """

    ADJ_CLOSE: Final = "adj_close"
    __TIMEFRAME: Final = "1d"

    def __init__(self, auto_adjust: bool = True):
        self.auto_adjust = auto_adjust

    def query(
        self,
        symbols: Union[str, Iterable[str]],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        _timeframe: Optional[str] = "",
        _adjust: Optional[Any] = None,
    ) -> pd.DataFrame:
        r"""Queries data from `Yahoo Finance <https://finance.yahoo.com/>`_\ .
        The timeframe of the data is limited to per day only.

        Args:
            symbols: Ticker symbols of the data to query.
            start_date: Start date of the data to query (inclusive).
            end_date: End date of the data to query (inclusive).

        Returns:
            :class:`pandas.DataFrame` containing the queried data.
        """
        return super().query(
            symbols, start_date, end_date, self.__TIMEFRAME, _adjust
        )

    def _fetch_data(
        self,
        symbols: frozenset[str],
        start_date: datetime,
        end_date: datetime,
        _timeframe: Optional[str],
        _adjust: Optional[Any],
    ) -> pd.DataFrame:
        df = yfinance.download(
            list(symbols),
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=self.auto_adjust,
        )
        if df.columns.empty:
            columns = [
                DataCol.SYMBOL.value,
                DataCol.DATE.value,
                DataCol.OPEN.value,
                DataCol.HIGH.value,
                DataCol.LOW.value,
                DataCol.CLOSE.value,
                DataCol.VOLUME.value,
            ]
            if not self.auto_adjust:
                columns.append(self.ADJ_CLOSE)
            return pd.DataFrame(columns=columns)
        if df.empty:
            return df
        df = df.reset_index()
        result = pd.DataFrame()
        if len(symbols) == 1:
            result[DataCol.DATE.value] = df["Date"].values
            result[DataCol.SYMBOL.value] = tuple(
                itertools.repeat(next(iter(symbols)), len(df["Close"].values))
            )
            result[DataCol.OPEN.value] = df["Open"].values
            result[DataCol.HIGH.value] = df["High"].values
            result[DataCol.LOW.value] = df["Low"].values
            result[DataCol.CLOSE.value] = df["Close"].values
            result[DataCol.VOLUME.value] = df["Volume"].values
            if not self.auto_adjust:
                result[self.ADJ_CLOSE] = df["Adj Close"].values
        else:
            df.columns = df.columns.to_flat_index()
            for sym in symbols:
                sym_df = pd.DataFrame()
                sym_df[DataCol.DATE.value] = df[("Date", "")].values
                sym_df[DataCol.SYMBOL.value] = tuple(
                    itertools.repeat(sym, len(df[("Close", sym)].values))
                )
                sym_df[DataCol.OPEN.value] = df[("Open", sym)].values
                sym_df[DataCol.HIGH.value] = df[("High", sym)].values
                sym_df[DataCol.LOW.value] = df[("Low", sym)].values
                sym_df[DataCol.CLOSE.value] = df[("Close", sym)].values
                sym_df[DataCol.VOLUME.value] = df[("Volume", sym)].values
                if not self.auto_adjust:
                    sym_df[self.ADJ_CLOSE] = df[("Adj Close", sym)].values
                result = pd.concat((result, sym_df))
        return result


class TiData(DataSource):
    """Retrieves data from the TradeInsight Trading Data Service.

    Uses the ``tidata`` client (``tidata.tifinance.Ticker``). Daily bars only.

    Args:
        api_key: TradeInsight API key, sent as a bearer token by the client.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key

    def _fetch_data(
        self,
        symbols: frozenset[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: Optional[str],
        adjust: Optional[Any],
    ) -> pd.DataFrame:
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")
        frames = []
        for sym in symbols:
            # raise_errors=True so auth/network failures propagate (and let the
            # provider chain fall through) instead of yielding an empty frame.
            hist = Ticker(sym, api_key=self._api_key).history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,
                actions=False,
                raise_errors=True,
            )
            if hist.empty:
                continue
            hist = hist.reset_index()  # 'Date' column, tz-naive
            frames.append(
                pd.DataFrame(
                    {
                        DataCol.DATE.value: hist["Date"],
                        DataCol.SYMBOL.value: sym,
                        DataCol.OPEN.value: hist["Open"],
                        DataCol.HIGH.value: hist["High"],
                        DataCol.LOW.value: hist["Low"],
                        DataCol.CLOSE.value: hist["Close"],
                        DataCol.VOLUME.value: hist["Volume"],
                    }
                )
            )
        if not frames:
            return pd.DataFrame(
                columns=[c.value for c in DataCol if c is not DataCol.VWAP]
            )
        return pd.concat(frames, ignore_index=True)
