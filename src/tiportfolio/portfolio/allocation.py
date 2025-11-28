from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, Tuple

from datetime import datetime

from src.tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from src.tiportfolio.portfolio.types import PortfolioConfig, TradingSignal
from src.tiportfolio.utils.logger import default_logger


class Allocation(ABC):

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[TradingAlgorithm],
    ) -> None:
        """Base class for portfolio allocation / rebalancing engines.

        Parameters
        ----------
        config:
            Portfolio configuration (time window, fees, initial capital, timeframe).
        strategies:
            List of tuples ``(symbol, history_data, strategy)``. ``history_data``
            must at least contain a ``"prices"`` DataFrame whose index is used
            as the walk‑forward timeline.
        """

        if not strategies:
            raise ValueError("data_and_strategies must contain at least one asset")

        # Keep as a list to preserve order and allow indexing
        self.config = config
        self.data_and_strategies = list(
            strategies
        )

        # Trade history: list of records where a trade occurs (signal change).
        # Each record is a dict with at least:
        # ["datetime", "symbol", "signal", "price", "value", "quantity",
        #  "fee_amount", "avg_cost", "unrealised_pnl"].
        self.trade_history: List[Dict[str, Any]] = []

        # Portfolio history: one record per (datetime, symbol), regardless of
        # whether a trade occurred. Same schema as trade_history.
        self.portfolio_history: List[Dict[str, Any]] = []

        # All price DataFrames should have the same index for time steps
        # (validated above).

    def walk_forward(self) -> List[Dict[str, Any]]:
        """Run a simple walk‑forward simulation.

        For each time step between ``config['time_start']`` and
        ``config['time_end']``, this will:

        1. Ask each strategy for its trading signal.
        2. Call :meth:`trigger_allocation` to get target portfolio weights.
        3. Record per‑symbol portfolio snapshots into ``portfolio_history``.
        4. Record trade events into ``trade_history`` whenever a symbol's
           signal changes compared to the previous step.

        The base implementation **does not** simulate cash/positions/PNL; it
        only orchestrates signal generation and allocation decisions and stores
        a lightweight accounting view of the portfolio.

        Returns
        -------
        list[dict]
            The full ``portfolio_history`` as a list of dictionaries. Each
            dictionary has the keys::

                "datetime", "symbol", "signal", "price", "value",
                "quantity", "fee_amount", "avg_cost", "unrealised_pnl".
        """

        datetime_start: datetime = self.config["time_start"]
        datetime_end: datetime = self.config["time_end"]

        # Use the first asset's prices index as the master timeline
        prices = self.data_and_strategies[0].prices_df
        prices_in_window = prices.loc[datetime_start:datetime_end]
        if prices_in_window.empty:
            raise ValueError("No price data available in the specified time window")

        # Clear any previous history before running a new walk‑forward.
        self.trade_history = []
        self.portfolio_history = []

        # Track previous signals per symbol in order to detect trades. We
        # assume an initial EXIT position if we have never seen a symbol
        # before. Signals are represented using :class:`TradingSignal`.
        previous_signals: Dict[str, TradingSignal] = {}

        for current_step in prices_in_window.index:
            default_logger.info(f"Current step: {current_step}")

            # 1. Collect signals from each strategy
            signals: Dict[str, TradingSignal] = {}
            for symbol, history_data, strategy in self.data_and_strategies:
                signal = strategy.execute(current_step)
                signals[symbol] = signal

            # 2. Run allocation to get target weights. Allocation operates
            # directly on :class:`TradingSignal` values.
            target_weights = self.trigger_allocation(current_step, signals)

            # 3. Record per‑symbol portfolio snapshot and detect trades.

            initial_capital = float(self.config["initial_capital"])

            for symbol, history_data, _ in self.data_and_strategies:
                prices_df = history_data["prices"]

                # Use the close price when available; otherwise fall back
                # to the first column for maximum compatibility with
                # minimal price DataFrames.
                try:
                    row = prices_df.loc[current_step]
                except KeyError:
                    # If there is no price for this exact timestamp, skip
                    # recording for this symbol at this step.
                    continue

                if "close" in row.index:
                    price = float(row["close"])
                else:
                    price = float(row.iloc[0])

                weight = float(target_weights.get(symbol, 0.0))
                notional_value = float(self.config["initial_capital"]) * weight

                quantity = 0.0
                if price > 0 and notional_value != 0:
                    quantity = notional_value / price

                record = {
                    "datetime": current_step,
                    "symbol": symbol,
                    "signal": signals.get(symbol, TradingSignal.EXIT),
                    "price": price,
                    "value": notional_value,
                    "quantity": quantity,
                    # Fees, average cost and unrealised PnL are placeholders
                    # in this minimal implementation and default to 0.0. A
                    # more sophisticated execution engine can populate them
                    # accurately.
                    "fee_amount": 0.0,
                    "avg_cost": price if quantity != 0 else 0.0,
                    "unrealised_pnl": 0.0,
                }

                # Portfolio history stores every step for every symbol.
                self.portfolio_history.append(record)

                # Trade history stores only steps where the signal changes
                # compared to the previous step.
                prev_signal = previous_signals.get(symbol, TradingSignal.EXIT)
                if record["signal"] != prev_signal:
                    self.trade_history.append(record.copy())
                    previous_signals[symbol] = record["signal"]

        return self.portfolio_history

    @abstractmethod
    def optimize_portfolio(self, current_step: datetime, signals: Dict[str, TradingSignal]) -> Dict[str, float]:
        """Optimize portfolio allocation for a given step.

        Parameters
        ----------
        current_step:
            Timestamp of the current step in the walk‑forward loop.
        signals:
            Mapping from symbol to trading signal produced by its strategy.
            Concrete implementations may choose to ignore signals if they use
            a purely fixed‑weight scheme.

        Returns
        -------
        dict[str, float]
            Target portfolio weights for each symbol. The base class does not
            enforce any normalisation, but typical implementations should
            ensure the weights sum to 1.0 for symbols that are in the
            portfolio.
        """
        raise NotImplementedError

    def trigger_allocation(self, current_step: datetime, signals: Dict[str, TradingSignal]) -> Dict[str, float]:
        """Wrapper around :meth:`optimize_portfolio`.

        This exists mainly as a hook for subclasses that may want to add
        logging, additional bookkeeping, or pre/post‑processing around the
        optimisation call.
        """

        return self.optimize_portfolio(current_step, signals)
