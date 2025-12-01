import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypedDict, Optional

from datetime import datetime

from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.utils.init_tz import init_tz

init_tz()  # todo move to main entry point


class PortfolioConfig(TypedDict):
    fees_config: FeesConfig
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

        self.config = config
        self.strategies = list(
            strategies
        )
        self.time_index = self.strategies[0].prices_df.index  # we assume all strategies have the same time index
        self.trade_history: List[Dict[str, Any]] = []
        self.portfolio_history: List[Dict[str, Any]] = []

    def walk_forward(self) -> None:
        if not self.time_index:
            raise ValueError("No price data available in the specified time window")

        for current_step in self.time_index:
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


