from __future__ import annotations

from datetime import datetime

import pandas as pd
from pandas import DataFrame

from tiportfolio.portfolio.trading import Trading, TradingAlgorithmConfig
from ...portfolio.types import TradingSignal


class SMACross(Trading):
    """
    Simple Moving Average (SMA) Crossover strategy.

        Long Short Hold Signal Only
    """

    def __init__(
            self,
            stock_symbol: str,
            prices: DataFrame,
            short_window: int = 10,
            long_window: int = 20,
    ) -> None:
        if short_window <= 0 or long_window <= 0:
            raise ValueError("short_window and long_window must be positive integers")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")

        # Store window configuration before calling the base class so that
        # :meth:`before_all` (invoked from ``TradingAlgorithm.__init__``)
        # can rely on these attributes being present.
        self.short_window = short_window
        self.long_window = long_window

        config: TradingAlgorithmConfig = {"set_signal_back": True}

        super().__init__(
            f"SMACross({short_window},{long_window})",
            stock_symbol,
            config=config,
            prices=prices,
        )

    def before_all(self) -> None:  # type: ignore[override]
        """Pre-compute rolling SMAs on the prices DataFrame.

        The rolling windows are applied in-place on ``self.prices_df`` so that
        the per-step signal evaluation only needs to read a tiny slice of the
        data. This keeps :meth:`_get_signal` simple and avoids look-ahead
        because :meth:`TradingAlgorithm.execute` always passes a slice limited
        to the current ``step``.
        """

        closes = self.dataframe["close"].astype(float)
        self.dataframe["sma_short"] = closes.rolling(
            window=self.short_window,
            min_periods=self.short_window,
        ).mean()
        self.dataframe["sma_long"] = closes.rolling(
            window=self.long_window,
            min_periods=self.long_window,
        ).mean()

    def run_at_step(self, history_prices: DataFrame, step: datetime) -> TradingSignal:  # type: ignore[override]
        """Return the SMA crossover signal at ``step``.

        ``history_prices`` is a slice of :attr:`prices_df` up to ``step``.
        We only inspect the final two rows (when available) to determine
        whether a golden or death cross has just occurred at the edge.
        """

        short_sma = history_prices["sma_short"]
        long_sma = history_prices["sma_long"]

        # if size smaller than 2, we cannot determine previous signal
        if len(history_prices) < 2:
            return TradingSignal.EXIT

        # If the latest long/short SMA is NaN, insufficient data, do not enter
        if pd.isna(long_sma.iloc[-1]) or pd.isna(short_sma.iloc[-1]):
            return TradingSignal.EXIT

        # Current SMA relationship defines bullish / bearish regime
        curr_short_sma = short_sma.iloc[-1]
        curr_long_sma = long_sma.iloc[-1]

        previous_short_sma = short_sma.iloc[-2]
        previous_long_sma = long_sma.iloc[-2]

        if pd.isna(previous_short_sma) or pd.isna(previous_long_sma) or pd.isna(curr_short_sma) or pd.isna(
                curr_long_sma):
            return TradingSignal.EXIT

        # Bullish regime: short SMA above long SMA
        if curr_short_sma > curr_long_sma and previous_short_sma < previous_long_sma:
            return TradingSignal.LONG
        elif curr_short_sma > curr_long_sma and previous_short_sma > previous_long_sma:
            return TradingSignal.LONG
        elif curr_short_sma < curr_long_sma and previous_short_sma > previous_long_sma:
            return TradingSignal.SHORT
        elif curr_short_sma < curr_long_sma and previous_short_sma < previous_long_sma:
            return TradingSignal.SHORT
        else:
            return TradingSignal.EXIT

    def after_all(self) -> None:  # type: ignore[override]
        """Optional post-run summary of generated signals.

        This mirrors the behaviour of :class:`LongHold` by counting how many
        LONG/HOLD/EXIT/SHORT signals were produced and printing a small
        summary. The method primarily exists to satisfy the
        :class:`TradingAlgorithm` abstract interface; tests do not rely on
        the printed output.
        """

        if "signal" not in self.dataframe.columns:
            return

        long_count = (self.dataframe["signal"] == TradingSignal.LONG.value).sum()
        exit_count = (self.dataframe["signal"] == TradingSignal.EXIT.value).sum()
        short_count = (self.dataframe["signal"] == TradingSignal.SHORT.value).sum()

        print(f"SMACross Strategy Summary for {self.symbol_stock} ({self.short_window},{self.long_window}):")
        print(f"  LONG signals: {long_count}")
        print(f"  EXIT signals: {exit_count}")
        print(f"  SHORT signals: {short_count}")
