from abc import ABC, abstractmethod
from typing import List, Generic, Tuple

from datetime import datetime

from pandas import DataFrame

from src.tiportfolio.portfolio.strategy import Strategy
from src.tiportfolio.portfolio.types import HistoryDataExtension, PortfolioConfig
from src.tiportfolio.utils.logger import default_logger


class Allocation(ABC, Generic[HistoryDataExtension]):

    def __init__(self, config: PortfolioConfig,
                 data_and_strategies: List[Tuple[str, HistoryDataExtension, Strategy[HistoryDataExtension]]]) -> None:
        self.config = config
        self.data_and_strategies = set(data_and_strategies)
        self.trading_history = DataFrame()

        # All dataframes should have the same index for time steps




    def walk_forward(self):
        """
        Walk Forward Simulation
        :return: dict of {symbol: weight}
        """

        datetime_start: datetime = self.config['time_start']
        datetime_end: datetime = self.config['time_end']


        for current_step in self.data_and_strategies[0][1]['prices'].loc[datetime_start:datetime_end].index:
            default_logger.info(f'Current step: {current_step}')

            # todo check record history and get current portfolio state

            # todo  run trigger allocation method



            for symbol, history_data, strategy in self.data_and_strategies:
                strategy.execute(
                    history_data, current_step
                )



            # todo record in trading history


            # todo generate metrics of performance, drawdown, sharpe ratio, etc. from record history






    @abstractmethod
    def optimize_portfolio(self, current_step: datetime,) -> tuple[str, float]:
        """
        Optimize Portfolio Allocation
        :param portfolio: dict of {symbol: weight}
        :param kwargs: other key word arguments
        :return: dict of {symbol: optimized_weight}
        """
        pass






    def trigger_allocation(self, current_step: datetime,) -> tuple[str, float]:
        return self.optimize_portfolio(current_step,)



