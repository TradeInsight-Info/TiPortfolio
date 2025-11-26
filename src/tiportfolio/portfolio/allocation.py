from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, Tuple

from datetime import datetime

from pandas import DataFrame

from src.tiportfolio.portfolio.strategy import Strategy
from src.tiportfolio.portfolio.types import HistoryDataExtension, PortfolioConfig
from src.tiportfolio.utils.logger import default_logger


class Allocation(ABC, Generic[HistoryDataExtension]):

    def __init__(
        self,
        config: PortfolioConfig,
        data_and_strategies: List[Tuple[str, HistoryDataExtension, Strategy[HistoryDataExtension]]],
    ) -> None:
        """Base class for portfolio allocation / rebalancing engines.

        Parameters
        ----------
        config:
            Portfolio configuration (time window, fees, initial capital, timeframe).
        data_and_strategies:
            List of tuples ``(symbol, history_data, strategy)``. ``history_data``
            must at least contain a ``"prices"`` DataFrame whose index is used
            as the walk‑forward timeline.
        """

        if not data_and_strategies:
            raise ValueError("data_and_strategies must contain at least one asset")

        # Keep as a list to preserve order and allow indexing
        self.config = config
        self.data_and_strategies: List[Tuple[str, HistoryDataExtension, Strategy[HistoryDataExtension]]] = list(
            data_and_strategies
        )

        # Basic input validation: ensure we have prices and aligned indices
        base_index = None
        for symbol, history_data, _ in self.data_and_strategies:
            if "prices" not in history_data:
                raise KeyError(f"history_data for symbol '{symbol}' must contain a 'prices' DataFrame")

            prices = history_data["prices"]
            if base_index is None:
                base_index = prices.index
            else:
                if not prices.index.equals(base_index):
                    raise ValueError(
                        "All 'prices' DataFrame indices must be identical across symbols "
                        "(same timestamps and order)."
                    )

        self.trading_history = DataFrame()

        # All dataframes should have the same index for time steps (validated above)




    def walk_forward(self) -> DataFrame:
        """Run a simple walk‑forward simulation.

        For each time step between ``config['time_start']`` and
        ``config['time_end']``, this will:

        1. Ask each strategy for its trading signal.
        2. Call :meth:`trigger_allocation` to get target portfolio weights.
        3. Record the step, signals and target weights into ``trading_history``.

        The base implementation **does not** simulate cash/positions/PNL; it
        only orchestrates signal generation and allocation decisions.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with one row per step and columns ``["datetime",
            "signals", "target_weights"]``. The ``signals`` and
            ``target_weights`` columns contain dictionaries keyed by symbol.
        """

        datetime_start: datetime = self.config["time_start"]
        datetime_end: datetime = self.config["time_end"]

        # Use the first asset's prices index as the master timeline
        prices = self.data_and_strategies[0][1]["prices"]
        prices_in_window = prices.loc[datetime_start:datetime_end]
        if prices_in_window.empty:
            raise ValueError("No price data available in the specified time window")

        records: List[Dict[str, Any]] = []

        for current_step in prices_in_window.index:
            default_logger.info(f"Current step: {current_step}")

            # 1. Collect signals from each strategy
            signals: Dict[str, int] = {}
            for symbol, history_data, strategy in self.data_and_strategies:
                signal = strategy.execute(history_data, current_step)
                signals[symbol] = int(signal)

            # 2. Run allocation to get target weights
            target_weights = self.trigger_allocation(current_step, signals)

            # 3. Record in trading history (simple record per timestamp)
            records.append(
                {
                    "datetime": current_step,
                    "signals": signals,
                    "target_weights": target_weights,
                }
            )

        self.trading_history = DataFrame.from_records(records)
        return self.trading_history






    @abstractmethod
    def optimize_portfolio(self, current_step: datetime, signals: Dict[str, int]) -> Dict[str, float]:
        """Optimize portfolio allocation for a given step.

        Parameters
        ----------
        current_step:
            Timestamp of the current step in the walk‑forward loop.
        signals:
            Mapping from symbol to trading signal produced by its strategy
            (1 = long, 0 = flat, -1 = short). Concrete implementations may
            choose to ignore signals if they use a purely fixed‑weight scheme.

        Returns
        -------
        dict[str, float]
            Target portfolio weights for each symbol. The base class does not
            enforce any normalisation, but typical implementations should
            ensure the weights sum to 1.0 for symbols that are in the
            portfolio.
        """
        raise NotImplementedError


    def trigger_allocation(self, current_step: datetime, signals: Dict[str, int]) -> Dict[str, float]:
        """Wrapper around :meth:`optimize_portfolio`.

        This exists mainly as a hook for subclasses that may want to add
        logging, additional bookkeeping, or pre/post‑processing around the
        optimisation call.
        """

        return self.optimize_portfolio(current_step, signals)


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
        data_and_strategies: List[Tuple[str, HistoryDataExtension, Strategy[HistoryDataExtension]]],
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



