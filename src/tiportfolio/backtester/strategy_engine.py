from typing import Union
from abc import ABC, abstractmethod

class StrategyEngine(ABC):
    def __init__(self, symbol, prices, config) -> None:
        """
        pairs, list of tuple (symbol, data frame)
        config: {
            'commission': 0.001,
            'risk_free_rate': 0.01,
        }
        """
        self.symbol = symbol
        self.prices = prices
        self.config = config


    @abstractmethod
    def trade_strategy(self, history_data, **kwargs) -> Union[1, -1, 0]:
        """
        Trade Strategy
        Pass history data and other parameters to decide how to trade it
        :param history_data: data frame
        :param kwargs: other key word arguments
        :return:
          1 for long, -1 for short, 0 for hold cash
        """
        pass


    def walk_forward(self):
        """
        Walk Forward Simulation
        1. Based on data frame from the earliest row (date time), walk to latest one
        2. At each step, use trade strategy method to decide how to trade it
        3. Record the trade history of each steps.

        :return: dataframe
          trade history
        """
        trade_history = []
        for index, row in self.prices.iterrows():
            history = self.prices.loc[:index]
            current_step_action = self.trade_strategy(history)
            trade_history.append({
                'datetime': index,
                'price': row['close'],
                'action': current_step_action
            })
        return trade_history


