from abc import ABC, abstractmethod
from typing import List, TypedDict, Optional, Tuple

import numpy as np
from pandas import DataFrame, MultiIndex, Timestamp
from tqdm import tqdm

from tiportfolio.portfolio.trading import Trading
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.utils.default_logger import logger
from tiportfolio.utils.init_tz import init_tz

init_tz()  # todo move to main entry point


class PortfolioConfig(TypedDict):
    fees_config: FeesConfig
    risk_free_rate: float
    initial_capital: float
    market_name: Optional[str]  # todo in the future support multiple markets


class PortfolioMetricsResult(TypedDict):
    final_value: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    annualized_return: float
    mar_ratio: float


class Allocation(ABC):

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[Trading],
    ) -> None:
        if not strategies:
            raise ValueError("data_and_strategies must contain at least one asset")

        self.config: PortfolioConfig = config
        self.strategies: List[Trading] = list(
            strategies
        )
        self.all_steps = self.strategies[0].all_steps  # we assume all strategies have the same time index
        self.portfolio_df: DataFrame = DataFrame(
            columns=[
                "signal",
                "open",
                "high",
                "low",
                "close",
                "quantity",
                "value",
                "fees",
                "cost_basis",
            ],
            index=MultiIndex.from_arrays([[], []], names=["datetime", "strategy_name"]),
        )
        self.strategy_ratio_map: dict[Tuple[Timestamp, str], float] = {}

    def is_first_step(self, current_step: Timestamp) -> bool:
        return current_step == self.all_steps[0]

    def is_last_step(self, current_step: Timestamp) -> bool:
        return current_step == self.all_steps[-1]

    def get_portfolio_snapshot(self, step: Timestamp) -> DataFrame:
        if step not in self.portfolio_df.index.get_level_values(0):
            raise ValueError(f"No portfolio data available for the given time step: {step}")

        snapshot = self.portfolio_df.xs(step, level='datetime')
        return snapshot

    def get_total_portfolio_value(self, step: Timestamp) -> float:
        snapshot = self.get_portfolio_snapshot(step)
        total_value = snapshot['value'].sum()
        return total_value

    def get_quantity(self, step: Timestamp, strategy_unique_name: str) -> float:
        idx = (step, strategy_unique_name)
        if idx not in self.portfolio_df.index:
            raise ValueError(f"No portfolio data available for the given time step and strategy: {idx}")

        quantity = self.portfolio_df.at[idx, 'quantity']
        return quantity

    def walk_forward(self) -> None:
        print("Starting walk-forward allocation process...")
        if self.all_steps.empty:
            raise ValueError("No price data available in the specified time window")

        for current_step in tqdm(self.all_steps):
            for strategy in self.strategies:
                signal_for_current_step = strategy.execute(current_step)
                logger.debug(
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
        fees, cost basis, etc. to fill self.portfolio_df.

        During the loop, get the allocation ratio from self.strategy_ratio_map
        (using the most recent rebalance date <= current step).
        """
        print("Starting portfolio evaluation...")
        if self.all_steps.empty:
            raise ValueError("No data available during evaluation")
        else:
            logger.info(f"Evaluating portfolio over {len(self.all_steps)} steps")

        all_rebalance_dates = set([date for (date, _) in self.strategy_ratio_map.keys()])
        previous_step: Optional[Timestamp] = None

        for step in tqdm(self.all_steps):
            for i in range(len(self.strategies)):
                strategy = self.strategies[i]
                # get quantity from previous step
                if previous_step and (previous_step, strategy.name) in self.portfolio_df.index:
                    previous_quantity = self.portfolio_df.at[(previous_step, strategy.name), 'quantity']
                    previous_cost_basis = self.portfolio_df.at[(previous_step, strategy.name), 'cost_basis']
                else:
                    previous_quantity = 0.0
                    previous_cost_basis = 0.0

                if previous_step:
                    previous_total_value = self.get_total_portfolio_value(previous_step)
                    # If previous portfolio value is 0 (no trades made yet), use initial_capital
                    if previous_total_value < 1e-10:
                        previous_total_value = self.config['initial_capital']
                    # Otherwise, keep the actual previous_total_value (don't override it)
                else:
                    previous_total_value = self.config['initial_capital']

                price_row = strategy.dataframe.loc[step]
                signal = price_row.get('signal', 0)

                if step in all_rebalance_dates:
                    logger.debug(f"Rebalance occurred at {step}")

                    # get target ratio for this rebalance date
                    target_ratio = self.strategy_ratio_map.get((step, strategy.name), 0.0)

                    if target_ratio is None:
                        logger.warning(f"No target ratio found for strategy {strategy.name} at rebalance date {step}")

                    # Find the most recent rebalance date <= previous_step
                    if previous_step:
                        previous_rebalance_dates = [d for d in all_rebalance_dates if d <= previous_step]
                        if previous_rebalance_dates:
                            most_recent_rebalance = max(previous_rebalance_dates)
                            previous_ratio = self.strategy_ratio_map.get((most_recent_rebalance, strategy.name), 0.0)
                        else:
                            previous_ratio = 0.0
                    else:
                        previous_ratio = 0.0
                    ratio_diff = target_ratio - previous_ratio

                    # amount to trade
                    trade_amount = ratio_diff * previous_total_value
                    quantity = previous_quantity + trade_amount / strategy.dataframe.at[step, 'close']

                    fees = self.config.get('fees_config', {}).get('commission',
                                                                  0.0) * trade_amount if trade_amount != 0 else 0.0
                    value = previous_total_value * target_ratio
                    cost_basis = previous_cost_basis + fees


                else:
                    logger.debug(f"No rebalance at {step}, log overall trade data")
                    quantity = previous_quantity

                    fees = 0.0  # no allocation change, so no fees
                    cost_basis = previous_cost_basis + fees
                    value = quantity * price_row['close']

                self.portfolio_df.loc[(step, strategy.name), :] = [
                    signal,
                    price_row['open'],
                    price_row['high'],
                    price_row['low'],
                    price_row['close'],
                    quantity,
                    value,
                    fees,
                    cost_basis,
                ]

            # keep track of the most recent rebalance date
            previous_step = step
            # sum all value for step to get total portfolio value
            total_value = self.get_total_portfolio_value(step)
            logger.debug(f"Total value: {total_value}")

    def get_metrics(self) -> PortfolioMetricsResult:
        """
        Calculate portfolio performance metrics from self.portfolio_df.

        Returns:
            PortfolioMetricsResult: Dictionary containing final_value,
                total_return, max_drawdown, sharpe_ratio, annualized_return,
                and mar_ratio.
        """
        if self.portfolio_df.empty:
            raise ValueError(
                "Portfolio DataFrame is empty. Run evaluate() first."
            )

        # Get all unique datetime steps
        unique_steps = sorted(
            self.portfolio_df.index.get_level_values(0).unique()
        )

        if len(unique_steps) < 2:
            raise ValueError(
                "Insufficient data to calculate metrics. "
                "Need at least 2 time steps."
            )

        # Calculate total portfolio value at each step
        portfolio_values = []
        for step in unique_steps:
            total_value = self.get_total_portfolio_value(step)
            portfolio_values.append(total_value)

        # Convert to numpy array for easier calculations
        values = np.array(portfolio_values)
        initial_capital = self.config['initial_capital']

        # Calculate period returns with protection against division by zero
        # Replace zeros in denominator with a small epsilon to avoid Inf/NaN
        denominator = values[:-1].copy()
        denominator[denominator == 0] = 1e-10
        period_returns = np.diff(values) / denominator
        # Replace any remaining NaN or Inf with 0.0
        period_returns = np.nan_to_num(period_returns, nan=0.0, posinf=0.0, neginf=0.0)

        # Calculate cumulative returns
        final_value = float(values[-1])
        total_return = (final_value - initial_capital) / initial_capital

        # Calculate drawdowns with protection against division by zero and NaN
        # Replace any NaN or Inf in values before calculation
        values_clean = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
        cumulative_max = np.maximum.accumulate(values_clean)
        # Replace zeros in cumulative_max with a small epsilon to avoid division by zero
        cumulative_max = np.where(cumulative_max == 0, 1e-10, cumulative_max)
        drawdowns = (values_clean / cumulative_max) - 1.0
        # Replace any NaN or Inf in drawdowns before taking min
        drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)
        max_drawdown = float(np.min(drawdowns))

        # Calculate annualized return
        num_trading_days = len(unique_steps) - 1
        if num_trading_days > 0:
            # Assuming 252 trading days per year
            years = num_trading_days / 252.0
            if years > 0:
                annualized_return = (
                        (1.0 + total_return) ** (1.0 / years) - 1.0
                )
            else:
                annualized_return = 0.0
        else:
            annualized_return = 0.0

        # Calculate Sharpe ratio with protection against invalid values
        risk_free_rate = self.config['risk_free_rate']
        if len(period_returns) > 1:
            # Filter out any remaining NaN/Inf values (shouldn't happen after previous fix, but be safe)
            valid_returns = period_returns[np.isfinite(period_returns)]
            if len(valid_returns) > 1:
                # Annualized volatility
                annualized_volatility = (
                        np.std(valid_returns, ddof=1) * np.sqrt(252.0)
                )
                # Ensure annualized_volatility is valid and positive
                if annualized_volatility > 1e-10 and np.isfinite(annualized_volatility):
                    sharpe_ratio = (
                            (annualized_return - risk_free_rate) /
                            annualized_volatility
                    )
                    # Ensure sharpe_ratio is finite
                    if not np.isfinite(sharpe_ratio):
                        sharpe_ratio = 0.0
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        # Calculate MAR ratio (return divided by max drawdown)
        max_dd_abs = abs(max_drawdown)
        if max_dd_abs > 1e-10:  # Protection against division by zero
            mar_ratio = total_return / max_dd_abs
        else:
            mar_ratio = 0.0

        result: PortfolioMetricsResult = {
            "final_value": final_value,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "annualized_return": annualized_return,
            "mar_ratio": mar_ratio,
        }

        return result
