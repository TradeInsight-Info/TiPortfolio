from abc import ABC, abstractmethod
from typing import List, TypedDict, Optional, Tuple

import numpy as np
from pandas import DataFrame, MultiIndex, Timestamp
from tqdm import tqdm

from tiportfolio.performance.metrics import calculate_portfolio_metrics
from tiportfolio.performance.plotting import plot_portfolio_value
from tiportfolio.portfolio.trading import Trading
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.utils.default_logger import logger
from tiportfolio.utils.init_tz import init_tz

init_tz()  # todo move to main entry point

# Cash strategy name constant
CASH_STRATEGY_NAME = "__CASH__"


class PortfolioConfig(TypedDict):
    commission: float
    slippage: float
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

        logger.info(
            f"Initialized Allocation with {len(self.strategies)} strategies with initial capital {self.config['initial_capital']}. "
        )
        # log all strategy names
        for strategy in self.strategies:
            logger.info(f" - Strategy: {strategy.name}")


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
        logger.info("Starting walk-forward allocation process...")
        if self.all_steps.empty:
            raise ValueError("No price data available in the specified time window")

        for current_step in tqdm(self.all_steps):
            for strategy in self.strategies:
                signal_for_current_step = strategy.execute(current_step)
                logger.debug(
                    f"At {current_step}, Strategy {strategy.name} generated signal: {signal_for_current_step}")

            if self.is_time_to_rebalance(current_step):
                logger.debug(f"Rebalancing at {current_step}")
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
        Cash is handled as a virtual strategy with price=1.0.
        """
        print("Starting portfolio evaluation...")
        if self.all_steps.empty:
            raise ValueError("No data available during evaluation")
        else:
            logger.info(f"Evaluating portfolio over {len(self.all_steps)} steps")

        all_rebalance_dates = set([date for (date, _) in self.strategy_ratio_map.keys()])
        previous_step: Optional[Timestamp] = None

        for step in tqdm(self.all_steps):
            # Get previous total portfolio value (cash + stocks)
            if previous_step:
                previous_total_value = self.get_total_portfolio_value(previous_step)
                if previous_total_value < 1e-10:
                    previous_total_value = self.config['initial_capital']
            else:
                previous_total_value = self.config['initial_capital']

            # Get or initialize cash quantity
            if previous_step and (previous_step, CASH_STRATEGY_NAME) in self.portfolio_df.index:
                cash_quantity = self.portfolio_df.at[(previous_step, CASH_STRATEGY_NAME), 'quantity']
            else:
                # First step: initialize cash with initial capital
                cash_quantity = self.config['initial_capital']

            # Calculate and store cash target ratio if rebalancing
            if step in all_rebalance_dates:
                cash_target_ratio = self.get_target_ratio(step, CASH_STRATEGY_NAME)
                # Store cash ratio in strategy_ratio_map
                self.strategy_ratio_map[(step, CASH_STRATEGY_NAME)] = cash_target_ratio

            # Process stock strategies first
            for i in range(len(self.strategies)):
                strategy = self.strategies[i]
                # get quantity from previous step
                if previous_step and (previous_step, strategy.name) in self.portfolio_df.index:
                    previous_quantity = self.portfolio_df.at[(previous_step, strategy.name), 'quantity']
                    previous_cost_basis = self.portfolio_df.at[(previous_step, strategy.name), 'cost_basis']
                else:
                    previous_quantity = 0.0
                    previous_cost_basis = 0.0

                price_row = strategy.dataframe.loc[step]
                signal = price_row.get('signal', 0)
                stock_price = price_row['close']

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

                    # Calculate fees
                    commission_rate = self.config.get('commission', 0.0)
                    fees = abs(trade_amount) * commission_rate if trade_amount != 0 else 0.0

                    # Update cash and quantity based on trade
                    if trade_amount > 0:  # Buying
                        # Reduce trade amount by fees before calculating shares
                        # This ensures fees reduce the purchase amount, not cash
                        net_trade_amount = trade_amount - fees
                        shares = net_trade_amount / stock_price
                        quantity = previous_quantity + shares
                        cash_quantity -= trade_amount  # Only deduct original trade_amount, fees already accounted for
                    elif trade_amount < 0:  # Selling
                        shares = abs(trade_amount) / stock_price
                        quantity = previous_quantity - shares
                        cash_quantity += (abs(trade_amount) - fees)
                    else:  # No trade
                        quantity = previous_quantity

                    value = quantity * stock_price
                    cost_basis = previous_cost_basis + fees

                else:
                    logger.debug(f"No rebalance at {step}, log overall trade data")
                    quantity = previous_quantity
                    fees = 0.0  # no allocation change, so no fees
                    cost_basis = previous_cost_basis + fees
                    value = quantity * stock_price

                self.portfolio_df.loc[(step, strategy.name), :] = [
                    signal,
                    price_row['open'],
                    price_row['high'],
                    price_row['low'],
                    stock_price,
                    quantity,
                    value,
                    fees,
                    cost_basis,
                ]

            # Handle cash strategy
            # On rebalance, cash was adjusted during stock trades above
            # Cash quantity should now be approximately: previous_total_value * cash_target_ratio - fees
            # On non-rebalance steps, cash quantity stays the same (already set above)

            # Store cash entry in portfolio_df
            self.portfolio_df.loc[(step, CASH_STRATEGY_NAME), :] = [
                0,  # signal (cash is always "hold")
                1.0,  # open
                1.0,  # high
                1.0,  # low
                1.0,  # close (always 1.0)
                cash_quantity,  # quantity
                cash_quantity,  # value = quantity * 1.0
                0.0,  # fees (cash doesn't have fees)
                0.0,  # cost_basis (cash doesn't have cost basis)
            ]

            # keep track of the most recent rebalance date
            previous_step = step
            # sum all value for step to get total portfolio value
            total_value = self.get_total_portfolio_value(step)
            logger.debug(f"Total value: {total_value}")

    def get_performance_metrics(
        self,
        plot: bool = False,
        fig_size: Tuple[float, float] = (12, 6),
        show_strategies: bool = True,
        show_rebalance_dates: bool = True,
        use_log_scale: bool = False,
    ) -> PortfolioMetricsResult:
        """
        Calculate portfolio performance metrics from self.portfolio_df.

        Args:
            plot: Whether to generate and display a plot of portfolio values.
            fig_size: Figure size (width, height) in inches. Only used if plot=True.
            show_strategies: Whether to show individual strategy values in plot.
                Only used if plot=True.
            show_rebalance_dates: Whether to mark rebalance dates in plot.
                Only used if plot=True.
            use_log_scale: Whether to use logarithmic scale for y-axis in plot.
                Only used if plot=True.

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

        # Convert to numpy array
        values = np.array(portfolio_values)
        initial_capital = self.config['initial_capital']

        # Calculate period returns from values
        denominator = values[:-1].copy()
        denominator[denominator == 0] = 1e-10
        period_returns = np.diff(values) / denominator
        period_returns = np.nan_to_num(period_returns, nan=0.0, posinf=0.0, neginf=0.0)

        # Calculate metrics using shared utility function
        num_trading_days = len(unique_steps) - 1
        metrics = calculate_portfolio_metrics(
            values=values,
            initial_capital=initial_capital,
            period_returns=period_returns,
            risk_free_rate=self.config['risk_free_rate'],
            num_trading_days=num_trading_days,
            calculate_sharpe=True,
            calculate_annualized=True,
        )

        result: PortfolioMetricsResult = {
            "final_value": metrics["final_value"],
            "total_return": metrics["total_return"],
            "max_drawdown": metrics["max_drawdown"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "annualized_return": metrics["annualized_return"],
            "mar_ratio": metrics["mar_ratio"],
        }

        # Generate plot if requested
        if plot:
            # Build strategy values dictionary
            strategy_values_dict: dict[str, list[float]] = {}
            strategy_names = sorted(
                self.portfolio_df.index.get_level_values(1).unique()
            )

            for strategy_name in strategy_names:
                strategy_values = []
                for step in unique_steps:
                    if (step, strategy_name) in self.portfolio_df.index:
                        value = self.portfolio_df.at[(step, strategy_name), "value"]
                        strategy_values.append(value)
                    else:
                        strategy_values.append(0.0)
                strategy_values_dict[strategy_name] = strategy_values

            # Get rebalance dates
            rebalance_dates = sorted(
                set([date for (date, _) in self.strategy_ratio_map.keys()])
            )

            # Call plotting utility function
            plot_portfolio_value(
                steps=unique_steps,
                portfolio_values=portfolio_values,
                strategy_values_dict=strategy_values_dict,
                rebalance_dates=rebalance_dates,
                figsize=fig_size,
                show_strategies=show_strategies,
                show_rebalance_dates=show_rebalance_dates,
                use_log_scale=use_log_scale,
            )

        return result
