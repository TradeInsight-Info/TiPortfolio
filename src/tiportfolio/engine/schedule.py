"""Schedule-based backtest engine."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from tiportfolio.backtest import BacktestResult
from tiportfolio.data import fetch_prices
from tiportfolio.engine.base import BacktestEngine


class ScheduleBasedEngine(BacktestEngine):
    """Backtest engine that fetches price data by symbol name.

    Use this engine when you want to pass a list of ticker symbols and a date
    range; it fetches OHLC data via Alpaca (if credentials are set) or Yahoo
    Finance, then runs the backtest.  For custom strategies that need VIX data
    or volatility-based rebalancing, use VolatilityBasedEngine instead.
    """

    def run(
        self,
        symbols: Iterable[str],
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        prices_df: dict[str, pd.DataFrame] | None = None,
        tz: str = "UTC",
    ) -> BacktestResult:
        """Run backtest by fetching prices for the given symbols and date range.

        If prices_df is provided and non-empty, use it as prices and do not fetch.
        Otherwise start and end are required and data is fetched via Alpaca or Yahoo Finance.
        """
        if prices_df is not None and len(prices_df) > 0:
            return super().run(prices=prices_df, start=start, end=end, tz=tz)
        if start is None or end is None:
            raise ValueError("start and end are required when not passing prices_df")
        prices = fetch_prices(symbols, start=start, end=end)
        return super().run(prices=prices, start=start, end=end, tz=tz)
