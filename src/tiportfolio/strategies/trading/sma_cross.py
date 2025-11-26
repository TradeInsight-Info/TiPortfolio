from __future__ import annotations

from typing import Union

import pandas as pd

from ...portfolio.strategy import Strategy


class SMACross(Strategy):
    """
    Simple Moving Average (SMA) Crossover strategy.

    Signals:
    - 1 when short SMA crosses above long SMA (golden cross)
    - -1 when short SMA crosses below long SMA (death cross)
    - 0 otherwise (including when insufficient data)
    """

    def __init__(self, short_window: int = 10, long_window: int = 20) -> None:
        if short_window <= 0 or long_window <= 0:
            raise ValueError("short_window and long_window must be positive integers")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")

        super().__init__(f"SMACross({short_window},{long_window})")
        self.short_window = short_window
        self.long_window = long_window

    # Implement the dunder hook using base class name-mangled identifier
    # so it properly overrides Strategy.__analyse_next_signal
    def _analyse_next_signal(self, history_data) -> Union[1, 0, -1]:  # type: ignore[override]
        prices: pd.DataFrame = history_data.get("prices")
        if prices is None or prices.empty:
            return 0

        # Ensure we have a 'close' column to compute SMAs
        if "close" not in prices.columns:
            return 0

        # Need at least long_window periods and 2 data points to check a cross
        if len(prices) < self.long_window or len(prices) < 2:
            return 0

        closes = prices["close"].astype(float)
        short_sma = closes.rolling(window=self.short_window, min_periods=self.short_window).mean()
        long_sma = closes.rolling(window=self.long_window, min_periods=self.long_window).mean()

        # If the latest long SMA is NaN, insufficient data
        if pd.isna(long_sma.iloc[-1]) or pd.isna(short_sma.iloc[-1]):
            return 0

        # Look at the last two observations to detect a cross at the edge
        prev_short = short_sma.iloc[-2]
        prev_long = long_sma.iloc[-2]
        curr_short = short_sma.iloc[-1]
        curr_long = long_sma.iloc[-1]

        # If previous values are NaN (can happen exactly when the first full long SMA appears)
        if pd.isna(prev_short) or pd.isna(prev_long):
            return 0

        # Golden cross
        if prev_short <= prev_long and curr_short > curr_long:
            return 1

        # Death cross
        if prev_short >= prev_long and curr_short < curr_long:
            return -1

        return 0
