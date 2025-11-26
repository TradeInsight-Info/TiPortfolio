from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, Tuple

from datetime import datetime

from pandas import DataFrame

from src.tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from src.tiportfolio.portfolio.types import HistoryDataExtension, PortfolioConfig
from src.tiportfolio.utils.logger import default_logger


class Allocation(ABC, Generic[HistoryDataExtension]):

    def __init__(
        self,
        config: PortfolioConfig,
        data_and_strategies: List[Tuple[str, HistoryDataExtension, TradingAlgorithm[HistoryDataExtension]]],
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
        self.data_and_strategies: List[Tuple[str, HistoryDataExtension, TradingAlgorithm[HistoryDataExtension]]] = list(
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



