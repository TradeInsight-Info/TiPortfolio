import logging
from abc import ABC, abstractmethod
from typing import List, TypedDict, Optional, Tuple

import numpy as np
import numba
from pandas import DataFrame, MultiIndex, Timestamp

from tiportfolio.portfolio.trading import Trading
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.utils.init_tz import init_tz

init_tz()  # todo move to main entry point


class PortfolioConfig(TypedDict):
    fees_config: FeesConfig
    risk_free_rate: float
    initial_capital: float
    market_name: Optional[str]  # todo in the future support multiple markets


@numba.jit(nopython=True)
def _evaluate_portfolio_numba(
    n_steps: int,
    n_strategies: int,
    # Input arrays (price data)
    prices_open: np.ndarray,      # [n_steps, n_strategies]
    prices_high: np.ndarray,      # [n_steps, n_strategies]
    prices_low: np.ndarray,       # [n_steps, n_strategies]
    prices_close: np.ndarray,     # [n_steps, n_strategies]
    prices_signal: np.ndarray,    # [n_steps, n_strategies]
    # Rebalance information
    rebalance_mask: np.ndarray,   # [n_steps] boolean
    target_ratios: np.ndarray,    # [n_steps, n_strategies]
    # Configuration
    initial_capital: float,
    commission_rate: float,
    # Output arrays (pre-allocated)
    out_signal: np.ndarray,
    out_open: np.ndarray,
    out_high: np.ndarray,
    out_low: np.ndarray,
    out_close: np.ndarray,
    out_quantity: np.ndarray,
    out_value: np.ndarray,
    out_fees: np.ndarray,
    out_cost_basis: np.ndarray,
) -> None:
    """
    JIT-compiled function to evaluate portfolio for all steps and strategies.
    Processes the evaluation loop efficiently using NumPy arrays.
    """
    # Track previous values for each strategy
    previous_quantities = np.zeros(n_strategies)
    previous_cost_bases = np.zeros(n_strategies)
    previous_ratios = np.zeros(n_strategies)
    previous_total_value = initial_capital

    for step_idx in range(n_steps):
        is_rebalance = rebalance_mask[step_idx]
        current_total_value = 0.0

        for strategy_idx in range(n_strategies):
            # Copy price data
            out_signal[step_idx, strategy_idx] = prices_signal[step_idx, strategy_idx]
            out_open[step_idx, strategy_idx] = prices_open[step_idx, strategy_idx]
            out_high[step_idx, strategy_idx] = prices_high[step_idx, strategy_idx]
            out_low[step_idx, strategy_idx] = prices_low[step_idx, strategy_idx]
            out_close[step_idx, strategy_idx] = prices_close[step_idx, strategy_idx]

            if is_rebalance:
                # Rebalance logic
                target_ratio = target_ratios[step_idx, strategy_idx]
                previous_ratio = previous_ratios[strategy_idx]
                ratio_diff = target_ratio - previous_ratio

                # Amount to trade
                trade_amount = ratio_diff * previous_total_value
                close_price = prices_close[step_idx, strategy_idx]

                # Calculate new quantity
                if close_price > 0.0:
                    quantity = previous_quantities[strategy_idx] + trade_amount / close_price
                else:
                    quantity = previous_quantities[strategy_idx]

                # Calculate fees
                if abs(trade_amount) > 1e-10:  # Avoid floating point issues
                    fees = commission_rate * abs(trade_amount)
                else:
                    fees = 0.0

                # Calculate value and cost basis
                value = previous_total_value * target_ratio
                cost_basis = previous_cost_bases[strategy_idx] + fees

                # Update previous ratios
                previous_ratios[strategy_idx] = target_ratio
            else:
                # No rebalance - maintain previous quantities
                quantity = previous_quantities[strategy_idx]
                fees = 0.0
                cost_basis = previous_cost_bases[strategy_idx]
                value = quantity * prices_close[step_idx, strategy_idx]

            # Store results
            out_quantity[step_idx, strategy_idx] = quantity
            out_value[step_idx, strategy_idx] = value
            out_fees[step_idx, strategy_idx] = fees
            out_cost_basis[step_idx, strategy_idx] = cost_basis

            # Update previous values for next iteration
            previous_quantities[strategy_idx] = quantity
            previous_cost_bases[strategy_idx] = cost_basis
            current_total_value += value

        # Update total value for next step
        previous_total_value = current_total_value


class Allocation(ABC):

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[Trading],
    ) -> None:
        if not strategies:
            raise ValueError("data_and_strategies must contain at least one asset")

        self.config: PortfolioConfig = config
        self.strategies: List[Trading] = list(strategies)
        self.all_steps = self.strategies[0].all_steps  # we assume all strategies have the same time index

        # Create index mappings
        n_steps = len(self.all_steps)
        n_strategies = len(self.strategies)

        self._step_to_idx: dict[Timestamp, int] = {step: idx for idx, step in enumerate(self.all_steps)}
        self._idx_to_step: list[Timestamp] = list(self.all_steps)
        self._strategy_to_idx: dict[str, int] = {strategy.name: idx for idx, strategy in enumerate(self.strategies)}
        self._idx_to_strategy: list[str] = [strategy.name for strategy in self.strategies]

        # Initialize NumPy arrays for internal storage
        # Shape: [n_steps, n_strategies]
        self._portfolio_data: dict[str, np.ndarray] = {
            'signal': np.full((n_steps, n_strategies), np.nan, dtype=np.float64),
            'open': np.full((n_steps, n_strategies), np.nan, dtype=np.float64),
            'high': np.full((n_steps, n_strategies), np.nan, dtype=np.float64),
            'low': np.full((n_steps, n_strategies), np.nan, dtype=np.float64),
            'close': np.full((n_steps, n_strategies), np.nan, dtype=np.float64),
            'quantity': np.zeros((n_steps, n_strategies), dtype=np.float64),
            'value': np.zeros((n_steps, n_strategies), dtype=np.float64),
            'fees': np.zeros((n_steps, n_strategies), dtype=np.float64),
            'cost_basis': np.zeros((n_steps, n_strategies), dtype=np.float64),
        }

        # Cached DataFrame (invalidated on writes)
        self._cached_portfolio_df: Optional[DataFrame] = None

        self.strategy_ratio_map: dict[Tuple[Timestamp, str], float] = {}

    @property
    def portfolio_df(self) -> DataFrame:
        """
        Lazy property that constructs DataFrame from NumPy arrays when needed.
        Caches the result for subsequent access.
        """
        if self._cached_portfolio_df is None:
            # Build MultiIndex
            datetime_index = [self._idx_to_step[step_idx] for step_idx in range(len(self.all_steps)) for _ in range(len(self.strategies))]
            strategy_index = [self._idx_to_strategy[strategy_idx] for _ in range(len(self.all_steps)) for strategy_idx in range(len(self.strategies))]

            # Build data dictionary
            data = {}
            for col in ['signal', 'open', 'high', 'low', 'close', 'quantity', 'value', 'fees', 'cost_basis']:
                # Flatten array: [n_steps, n_strategies] -> [n_steps * n_strategies]
                data[col] = self._portfolio_data[col].flatten()

            # Create MultiIndex
            index = MultiIndex.from_arrays([datetime_index, strategy_index], names=["datetime", "strategy_name"])

            # Create DataFrame
            self._cached_portfolio_df = DataFrame(data, index=index)

        return self._cached_portfolio_df

    def _invalidate_portfolio_df_cache(self) -> None:
        """Invalidate cached DataFrame when data is modified."""
        self._cached_portfolio_df = None

    def is_first_step(self, current_step: Timestamp) -> bool:
        return current_step == self.all_steps[0]

    def is_last_step(self, current_step: Timestamp) -> bool:
        return current_step == self.all_steps[-1]

    def get_portfolio_snapshot(self, step: Timestamp) -> DataFrame:
        """Get portfolio snapshot for a specific step."""
        if step not in self._step_to_idx:
            raise ValueError(f"No portfolio data available for the given time step: {step}")

        step_idx = self._step_to_idx[step]
        n_strategies = len(self.strategies)

        # Build data dictionary from array slices
        data = {}
        for col in ['signal', 'open', 'high', 'low', 'close', 'quantity', 'value', 'fees', 'cost_basis']:
            data[col] = self._portfolio_data[col][step_idx, :]

        # Create DataFrame with strategy names as index
        index = [self._idx_to_strategy[i] for i in range(n_strategies)]
        snapshot = DataFrame(data, index=index)
        snapshot.index.name = 'strategy_name'

        return snapshot

    def get_total_portfolio_value(self, step: Timestamp) -> float:
        """Get total portfolio value for a specific step."""
        if step not in self._step_to_idx:
            raise ValueError(f"No portfolio data available for the given time step: {step}")

        step_idx = self._step_to_idx[step]
        return float(np.sum(self._portfolio_data['value'][step_idx, :]))

    def get_quantity(self, step: Timestamp, strategy_unique_name: str) -> float:
        """Get quantity for a specific step and strategy."""
        if step not in self._step_to_idx:
            raise ValueError(f"No portfolio data available for the given time step: {step}")
        if strategy_unique_name not in self._strategy_to_idx:
            raise ValueError(f"No portfolio data available for strategy: {strategy_unique_name}")

        step_idx = self._step_to_idx[step]
        strategy_idx = self._strategy_to_idx[strategy_unique_name]
        return float(self._portfolio_data['quantity'][step_idx, strategy_idx])

    def walk_forward(self) -> None:
        """Walk forward through time steps and execute strategies."""
        if self.all_steps.empty:
            raise ValueError("No price data available in the specified time window")

        # Pre-compute step indices to avoid repeated get_loc() calls
        step_indices = {step: self._step_to_idx[step] for step in self.all_steps}

        for current_step in self.all_steps:
            for strategy in self.strategies:
                signal_for_current_step = strategy.execute(current_step)
                logging.debug(
                    f"At {current_step}, Strategy {strategy.name} generated signal: {signal_for_current_step}")

            if self.is_time_to_rebalance(current_step):
                for strategy in self.strategies:
                    target_ratio = self.get_target_ratio(current_step, strategy.name)
                    self.set_target_ratio(current_step, strategy.name, target_ratio)

    def set_target_ratio(self, current_step: Timestamp, strategy_name: str, target_ratio: float) -> None:
        if not (0.0 <= target_ratio <= 1.0):
            raise ValueError("Target ratio must be between 0.0 and 1.0")
        self.strategy_ratio_map[(current_step, strategy_name)] = target_ratio

    @abstractmethod
    def get_target_ratio(self, current_step: Timestamp, strategy_name: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def is_time_to_rebalance(self, current_step: Timestamp) -> bool:
        raise NotImplementedError

    def evaluate(self) -> None:
        """
        Loop through all steps and strategies to calculate portfolio value,
        fees, cost basis, etc. using NumPy arrays and numba JIT compilation.

        During the loop, get the allocation ratio from self.strategy_ratio_map
        (using the most recent rebalance date <= current step).
        """
        if self.all_steps.empty:
            raise ValueError("No price data available")

        n_steps = len(self.all_steps)
        n_strategies = len(self.strategies)

        # Extract price data to NumPy arrays (one-time cost)
        prices_open = np.zeros((n_steps, n_strategies), dtype=np.float64)
        prices_high = np.zeros((n_steps, n_strategies), dtype=np.float64)
        prices_low = np.zeros((n_steps, n_strategies), dtype=np.float64)
        prices_close = np.zeros((n_steps, n_strategies), dtype=np.float64)
        prices_signal = np.zeros((n_steps, n_strategies), dtype=np.float64)

        for step_idx, step in enumerate(self.all_steps):
            for strategy_idx, strategy in enumerate(self.strategies):
                price_row = strategy.dataframe.loc[step]
                prices_open[step_idx, strategy_idx] = float(price_row['open'])
                prices_high[step_idx, strategy_idx] = float(price_row['high'])
                prices_low[step_idx, strategy_idx] = float(price_row['low'])
                prices_close[step_idx, strategy_idx] = float(price_row['close'])
                prices_signal[step_idx, strategy_idx] = float(price_row.get('signal', 0))

        # Build rebalance mask and target ratios array
        all_rebalance_dates = set([date for (date, _) in self.strategy_ratio_map.keys()])
        rebalance_mask = np.zeros(n_steps, dtype=np.bool_)
        target_ratios = np.zeros((n_steps, n_strategies), dtype=np.float64)

        # Track the most recent ratio for each strategy (for non-rebalance steps)
        # We need to find the most recent rebalance date <= current step
        current_ratios = {strategy.name: 0.0 for strategy in self.strategies}

        for step_idx, step in enumerate(self.all_steps):
            if step in all_rebalance_dates:
                rebalance_mask[step_idx] = True
                # Update target ratios for this rebalance date
                for strategy_idx, strategy in enumerate(self.strategies):
                    target_ratio = self.strategy_ratio_map.get((step, strategy.name), 0.0)
                    if target_ratio is None:
                        logging.warning(f"No target ratio found for strategy {strategy.name} at rebalance date {step}")
                        target_ratio = 0.0
                    target_ratios[step_idx, strategy_idx] = target_ratio
                    current_ratios[strategy.name] = target_ratio
            else:
                # Use the most recent ratio (from previous rebalance)
                for strategy_idx, strategy in enumerate(self.strategies):
                    target_ratios[step_idx, strategy_idx] = current_ratios[strategy.name]

        # Get commission rate from config
        commission_rate = float(self.config.get('fees_config', {}).get('commission', 0.0))
        initial_capital = float(self.config['initial_capital'])

        # Call numba-compiled function to fill output arrays
        _evaluate_portfolio_numba(
            n_steps=n_steps,
            n_strategies=n_strategies,
            prices_open=prices_open,
            prices_high=prices_high,
            prices_low=prices_low,
            prices_close=prices_close,
            prices_signal=prices_signal,
            rebalance_mask=rebalance_mask,
            target_ratios=target_ratios,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            out_signal=self._portfolio_data['signal'],
            out_open=self._portfolio_data['open'],
            out_high=self._portfolio_data['high'],
            out_low=self._portfolio_data['low'],
            out_close=self._portfolio_data['close'],
            out_quantity=self._portfolio_data['quantity'],
            out_value=self._portfolio_data['value'],
            out_fees=self._portfolio_data['fees'],
            out_cost_basis=self._portfolio_data['cost_basis'],
        )

        # Invalidate cached DataFrame
        self._invalidate_portfolio_df_cache()

        # Log total value for last step (for debugging)
        if n_steps > 0:
            last_step = self._idx_to_step[n_steps - 1]
            total_value = self.get_total_portfolio_value(last_step)
            logging.debug(f"Total value: {total_value}")

    def get_metrics(self):
        # user self.portfolio_df to calculate metrics like total return, max drawdown, etc.
        pass
