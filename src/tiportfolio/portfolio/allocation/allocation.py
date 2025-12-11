import logging
from abc import ABC, abstractmethod
from ftplib import all_errors
from typing import List, TypedDict, Optional, Mapping, Tuple

from datetime import datetime

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
            index=MultiIndex.from_arrays([[], []], names=["datetime", "strategy_unique_name"]),
        )
        self.strategy_ratio_map: Mapping[Tuple[Timestamp, str], float] = {}

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

        quantity = self.portfolio_df.loc[idx, 'quantity']
        return quantity



    def walk_forward(self) -> None:
        if self.all_steps.empty:
            raise ValueError("No price data available in the specified time window")

        for current_step in self.all_steps:
            for strategy in self.strategies:
                signal_for_current_step = strategy.execute(current_step)
                logging.debug(
                    f"At {current_step}, Strategy {strategy.name} generated signal: {signal_for_current_step}")
            if self.is_time_to_rebalance(current_step):
                self.rebalance(current_step)

    @abstractmethod
    def rebalance(self, current_step: datetime, ) -> None:
        """
        Record time step to rebalance and the target ratio
        :param current_step:
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def is_time_to_rebalance(self, current_step: datetime) -> bool:
        raise NotImplementedError

    def evaluate(self) -> None:
        """
        Loop through all steps and strategies to calculate portfolio value,
        fees, cost basis, etc. to fill self.portfolio_df.

        During the loop, get the allocation ratio from self.strategy_ratio_map
        (using the most recent rebalance date <= current step).
        """
        if self.all_steps.empty:
            raise ValueError("No price data available")

        all_rebalance_dates = set([date for (date, _) in self.strategy_ratio_map.keys()])
        previous_rebalance_date: Optional[Timestamp] = None

        for step in self.all_steps:

            if step in all_rebalance_dates:
                logging.debug(f"Rebalance occurred at {step}")

                for strategy in self.strategies:
                    # get target ratio for this rebalance date
                    target_ratio = self.strategy_ratio_map.get((step, str(strategy)), None)

                    if target_ratio is None:
                        logging.warning(f"No target ratio found for strategy {strategy} at rebalance date {step}")


                    previous_ratio = self.strategy_ratio_map.get((previous_rebalance_date, str(strategy)), 0.0)
                    ratio_diff = target_ratio - previous_ratio


            else:
                logging.debug(f"No rebalance at {step}")

                # based on strategy signal, write down data to columns of self.portfolio_df
                for strategy in self.strategies:
                    price_row = strategy.dataframe.loc[step]
                    signal = price_row.get('signal', 0)

                    quantity = (self.config['initial_capital'] * ratio) / price_row['close'] if signal != 0 else 0.0
                    value = quantity * price_row['close']
                    fees = value * self.config['fees_config'].get('commission', 0.0)
                    cost_basis = value + fees

                    self.portfolio_df.loc[(step, strategy_name), :] = [
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





    def get_metrics(self):
        # user self.portfolio_df to calculate metrics like total return, max drawdown, etc.
        pass