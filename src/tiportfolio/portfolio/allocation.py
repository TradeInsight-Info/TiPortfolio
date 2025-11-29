import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypedDict, Optional

from datetime import datetime, timedelta

from src.tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from src.tiportfolio.portfolio.types import FeesConfig


class PortfolioConfig(TypedDict):
    fees_config: FeesConfig
    initial_capital: float
    time_start: Optional[datetime]
    time_end: Optional[datetime]
    timeframe: Optional[timedelta]


class Allocation(ABC):

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[TradingAlgorithm],
    ) -> None:
        if not strategies:
            raise ValueError("data_and_strategies must contain at least one asset")

        # Keep as a list to preserve order and allow indexing
        self.config = config
        self.strategies = list(
            strategies
        )
        self.trade_history: List[Dict[str, Any]] = []
        self.portfolio_history: List[Dict[str, Any]] = []

    def walk_forward(self) -> None:
        first_prices_df = self.strategies[0].prices_df
        # get index start and end from first strategy prices dataframe
        prices_df_in_window = first_prices_df
        if prices_df_in_window.empty:
            raise ValueError("No price data available in the specified time window")

        for current_step in prices_df_in_window.index:
            if self.is_time_to_rebalance(current_step):
                self.rebalance(current_step)

            for strategy in self.strategies:
                signal = strategy.execute(current_step)
                logging.debug(f"At {current_step}, Strategy {strategy.strategy_name} generated signal: {signal}")

    @abstractmethod
    def rebalance(self, current_step: datetime, ) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_time_to_rebalance(self, current_step: datetime) -> bool:
        raise NotImplementedError
