import logging
from abc import ABC, abstractmethod
from typing import List, TypedDict, Optional

from datetime import datetime

from pandas import DataFrame, MultiIndex, Timestamp

from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
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
            strategies: List[TradingAlgorithm],
    ) -> None:
        if not strategies:
            raise ValueError("data_and_strategies must contain at least one asset")

        self.config: PortfolioConfig = config
        self.strategies: List[TradingAlgorithm] = list(
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


    def get_metrics(self):
        # user self.portfolio_df to calculate metrics like total return, max drawdown, etc.
        pass






    def walk_forward(self) -> None:
        if self.all_steps.empty:
            raise ValueError("No price data available in the specified time window")

        for current_step in self.all_steps:

            for strategy in self.strategies:
                signal_for_current_step = strategy.execute(current_step)
                logging.debug(
                    f"At {current_step}, Strategy {strategy.unique_name} generated signal: {signal_for_current_step}")

                price_row = strategy.prices_df.loc[current_step]
                idx = (current_step, strategy.unique_name)
                self.portfolio_df.loc[idx] = {
                    'open': price_row['open'],
                    'high': price_row['high'],
                    'low': price_row['low'],
                    'close': price_row['close'],
                    'signal': signal_for_current_step.value,
                }
            if self.is_time_to_rebalance(current_step):
                self.rebalance(current_step)

    @abstractmethod
    def rebalance(self, current_step: datetime, ) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_time_to_rebalance(self, current_step: datetime) -> bool:
        raise NotImplementedError
