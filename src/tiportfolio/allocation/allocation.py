


from abc import ABC, abstractmethod
from typing import TypedDict, Generic, Union, Tuple

from typing import TypeVar, TypedDict, Optional, List, Union, Callable, TypeAlias

from pandas import DataFrame
from datetime import datetime



class StrategyData(TypedDict):
    prices: DataFrame  # DataFrame with price data, with columns['open', 'high', 'low', 'close', 'volume']
    other_datas: Optional[List[DataFrame]]  # DataFrame with other data, e.g. indicators


class TradingConfig(TypedDict):
    commission: float
    slippage: float
    risk_free_rate: float



class PortfolioConfig(TypedDict):
    trading_config: TradingConfig
    initial_capital: float


StrategyDataType = Union[DataFrame, List[DataFrame]]

StrategyFunction: TypeAlias = Callable[
    [StrategyDataType], Union[1, -1, 0]]  # A strategy function that returns 1 (long), -1 (short), or 0 (hold)


class Allocation(ABC):

    def __init__(self, config:PortfolioConfig, strategies: List[Tuple[StrategyData, StrategyFunction]]) -> None:
        self.config = config
        self.strategies = strategies


    def walk_forward(self, current_step:datetime):
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


