


from abc import ABC, abstractmethod
from typing import TypedDict, Tuple


class TradingConfig(TypedDict):
    commission: float
    slippage: float
    risk_free_rate: float



class PortfolioConfig(TypedDict):
    trading_config: TradingConfig
    initial_capital: float




class Allocation(ABC):

    def __init__(self, config:PortfolioConfig, **kwargs) -> None:
        self.config = config


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


    def walk_forward(self, portfolio_history):
        """
        Walk Forward Simulation for Portfolio Allocation
        1. Based on portfolio history from the earliest date to the latest one
        2. At each step, use optimize_portfolio method to decide how to allocate it
        3. Record the allocation history of each step.

        :param portfolio_history: list of dict of {symbol: weight}
        :return: list of dict of {symbol: optimized_weight}
        """
        pass