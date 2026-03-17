"""Base backtest engine."""

from __future__ import annotations

from abc import ABC

import pandas as pd

from tiportfolio.allocation import AllocationStrategy, FixRatio
from tiportfolio.backtest import BacktestResult, run_backtest
from tiportfolio.calendar import Schedule, normalize_price_index
from tiportfolio.data import normalize_prices


class BacktestEngine(ABC):
    """Engine for running backtests with AllocationStrategy and scheduled rebalance."""

    def __init__(
        self,
        *,
        allocation: FixRatio | AllocationStrategy,
        rebalance: Schedule,
        fee_per_share: float = 0.0035,
        initial_value: float = 10000.0,
        risk_free_rate: float = 0.04,
        signal_delay: int = 1,
    ) -> None:
        if signal_delay < 0:
            raise ValueError(f"signal_delay must be >= 0; got {signal_delay}")
        self.allocation = allocation
        self.rebalance = rebalance
        self.fee_per_share = fee_per_share
        self.initial_value = initial_value
        self.risk_free_rate = risk_free_rate
        self.signal_delay = signal_delay

    def run(
        self,
        prices: dict[str, pd.DataFrame],
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        tz: str = "UTC",
    ) -> BacktestResult:
        """Run backtest. prices: dict symbol -> DataFrame (date index, OHLC columns). tz: timezone for normalization."""
        allocation_keys = set(self.allocation.get_symbols())

        for symbol, df in prices.items():
            if not all(col in df.columns for col in ["open", "high", "low", "close"]):
                raise ValueError(f"DataFrame for {symbol!r} missing required OHLC columns")

        prices = {symbol: normalize_price_index(df, tz=tz) for symbol, df in prices.items()}
        prices_df = normalize_prices(prices, allocation_keys)
        return run_backtest(
            prices_df,
            self.allocation,
            self.rebalance.spec,
            self.fee_per_share,
            start=start,
            end=end,
            initial_value=self.initial_value,
            risk_free_rate=self.risk_free_rate,
            signal_delay=self.signal_delay,
        )
