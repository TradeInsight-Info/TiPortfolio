from abc import ABC, abstractmethod
from typing import TypedDict, Optional, List, Union, Generic, Tuple

from pandas import DataFrame
from datetime import datetime

from src.tiportfolio.allocation.types import HistoryDataExtension


class StrategyData(TypedDict):
    prices: DataFrame  # DataFrame with price data, with columns['open', 'high', 'low', 'close', 'volume']
    other_datas: Optional[List[DataFrame]]  # DataFrame with other data, e.g. indicators


class BrokerConfig(TypedDict):
    commission: float
    slippage: float
    risk_free_rate: float


class PortfolioConfig(TypedDict):
    broker_config: BrokerConfig
    initial_capital: float
    datetime_start: datetime
    datetime_end: datetime
    timeframe: str  # e.g. '1d', '1h' etc. todo validate format


class Strategy(ABC, Generic[HistoryDataExtension]):

    def __init__(self, name) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"Strategy({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)

    @abstractmethod
    def execute(self, history_data: HistoryDataExtension) -> Union[1, 0, -1]:
        """
        Generate trading signals using the strategy function
        :return: DataFrame with signals
        """
        pass


class Allocation(ABC, Generic[HistoryDataExtension]):

    def __init__(self, config: PortfolioConfig,
                 data_and_strategies: List[Tuple[str, HistoryDataExtension, Strategy[HistoryDataExtension]]]) -> None:
        self.config = config
        self.data_and_strategies = set(data_and_strategies)

    def walk_forward(self, current_step: datetime):
        pass

    @abstractmethod
    def optimize_portfolio(self, portfolio, **kwargs):
        """
        Optimize Portfolio Allocation
        :param portfolio: dict of {symbol: weight}
        :param kwargs: other key word arguments
        :return: dict of {symbol: optimized_weight}
        """
        pass

    @abstractmethod
    def trigger_allocation(self, market_data, **kwargs):
        """
        Trigger Portfolio Allocation based on Market Data
        :param market_data: dict of {symbol: data frame}
        :param kwargs: other key word arguments
        :return: dict of {symbol: weight}
        """
        pass
