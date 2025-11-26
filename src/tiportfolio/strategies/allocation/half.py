from datetime import datetime
from typing import List, Tuple, Dict

from tiportfolio.portfolio.allocation import Allocation
from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from tiportfolio.portfolio.types import HistoryDataExtension, PortfolioConfig


class FixedAllocation50_50(Allocation[HistoryDataExtension]):
    """Simple two‑asset allocation with fixed 50/50 monthly rebalancing.

    This allocation engine assumes **exactly two** assets are provided.
    It keeps the portfolio at 50% / 50% notional weight for each asset,
    rebalancing at the **start of each new month**. Between rebalancing
    dates, it lets weights drift according to relative price movements.

    A rebalance decision is made as follows:

    * On each step, current notional values are updated based on price
      changes since the previous step.
    * When a new calendar month starts (compared to the last rebalance
      date), current weights are computed from these values.
    * If one asset's weight exceeds 50% (e.g. 55%), the allocation is
      reset to exactly 50/50 by notionally "selling" the overweight asset
      and "buying" the underweight one.

    The class only returns target weights; order sizing, fees, and
    execution details are intentionally out of scope for this minimal
    implementation.
    """

    def __init__(
        self,
        config: PortfolioConfig,
        data_and_strategies: List[Tuple[str, HistoryDataExtension, TradingAlgorithm[HistoryDataExtension]]],
    ) -> None:
        super().__init__(config, data_and_strategies)

        if len(self.data_and_strategies) != 2:
            raise ValueError(
                "FixedAllocation50_50 requires exactly two assets in data_and_strategies"
            )

        # Preserve the symbol order in the provided list
        self.symbols: List[str] = [item[0] for item in self.data_and_strategies]

        # Initialise notional values to split the initial capital 50/50
        initial_capital = float(self.config["initial_capital"])
        half_capital = initial_capital / 2.0
        self._current_values: Dict[str, float] = {
            self.symbols[0]: half_capital,
            self.symbols[1]: half_capital,
        }

        # Track previous step and last rebalance month/year
        self._last_step: datetime | None = None
        self._last_rebalance_year: int | None = None
        self._last_rebalance_month: int | None = None

    def _update_values_for_step(self, current_step: datetime) -> None:
        """Update current notional values using price relatives from last step.

        This assumes we hold a fixed number of units between rebalances,
        so value changes in proportion to price changes.
        """

        if self._last_step is None:
            # Nothing to update on the very first step
            self._last_step = current_step
            return

        for symbol, history_data, _ in self.data_and_strategies:
            prices = history_data["prices"]["close"]

            # Guard against missing timestamps; if either price is missing,
            # skip value update for that symbol.
            try:
                prev_price = float(prices.loc[self._last_step])
                curr_price = float(prices.loc[current_step])
            except KeyError:
                continue

            if prev_price <= 0:
                continue

            rel = curr_price / prev_price
            self._current_values[symbol] = self._current_values.get(symbol, 0.0) * rel

        self._last_step = current_step

    def _current_weights(self) -> Dict[str, float]:
        total = sum(self._current_values.values())
        if total <= 0:
            # Avoid division by zero; fall back to equal weights
            return {symbol: 0.5 for symbol in self.symbols}
        return {symbol: self._current_values[symbol] / total for symbol in self.symbols}

    def optimize_portfolio(self, current_step: datetime, signals: Dict[str, int]) -> Dict[str, float]:
        """Return target 50/50 allocation with monthly rebalancing.

        ``signals`` are currently ignored; this allocator is purely
        allocation‑driven and does not react to strategy outputs.
        """

        _ = signals  # explicitly ignore, but keep signature for future use

        # Update values based on price moves since the last step
        self._update_values_for_step(current_step)

        year = current_step.year
        month = current_step.month

        # Determine if we should rebalance at this step
        should_rebalance = False
        if self._last_rebalance_year is None or self._last_rebalance_month is None:
            should_rebalance = True
        elif (year, month) != (self._last_rebalance_year, self._last_rebalance_month):
            should_rebalance = True

        if should_rebalance:
            weights = self._current_weights()
            # If any asset is above 50%, rebalance to exact 50/50
            overweight = any(w > 0.5 for w in weights.values())
            if overweight:
                total_value = sum(self._current_values.values())
                new_value_each = total_value * 0.5
                for symbol in self.symbols:
                    self._current_values[symbol] = new_value_each

            # Record that we have rebalanced this month
            self._last_rebalance_year = year
            self._last_rebalance_month = month

        # Target weights are always 50/50 by design
        return {symbol: 0.5 for symbol in self.symbols}
