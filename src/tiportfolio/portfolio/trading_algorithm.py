from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypedDict, List

from pandas import DataFrame

from .types import TradingSignal
from ..utils.constants import BASIC_REQUIRED_COLUMNS


class TradingAlgorithmConfig(TypedDict, total=False):
    set_signal_back: bool


class TradingAlgorithm(ABC):

    def __init__(self, name: str, symbol: str, *, prices: DataFrame, config: TradingAlgorithmConfig = None,
                 **other_data: DataFrame, ) -> None:
        """
        Initialize Trading Strategy
            Pass your extra data as keyword arguments
        :param name:
        :param symbol:
        :param **kwargs: HistoryDataExtension | TradingAlgorithmConfig,
                It must have 'prices' key with DataFrame containing at least ['open', 'high', 'low', 'close'] columns
                We pass data frame in a mutable way to avoid copying large data frames for performance reasons
        """
        self._name = name
        self._symbol = symbol
        self._set_signal_back = config.get('set_signal_back', False)
        for col in BASIC_REQUIRED_COLUMNS:
            if col not in prices.columns:
                raise ValueError(f"Data['prices'] must have '{col}' column")

        self._prices: DataFrame = prices
        self.before_all()

    def __str__(self) -> str:
        return f"Strategy({self._name} - {self._symbol})"

    def __hash__(self) -> int:
        return hash(self._name + self._symbol)

    @property
    def strategy_name(self) -> str:
        return self.__str__()

    @property
    def prices_df(self) -> DataFrame:
        return self._prices

    def set_signal_back_to_prices_df(self, step: datetime, signal: TradingSignal) -> None:
        """
        Post run actions after each _get_signal step is complete
        We can update the column 'signal' in the prices DataFrame here
        :return: None
        """
        self._prices.loc[step, 'signal'] = signal.value

    def execute(self, step: datetime) -> TradingSignal:
        """
        Generate trading signals using the strategy function
        :param step: datetime
        :return: TradingSignal
        """
        signal = self._run(
            self._prices.loc[:step],  # we use the loc to avoid look-ahead bias
            step,
        )
        if self._set_signal_back:
            self.set_signal_back_to_prices_df(step, signal)
        return signal

    @abstractmethod
    def before_all(self) -> None:
        """
        Prepare History Data for Analysis
        Update the data in place for example, adding indicators as a new columns to the prices DataFrame
        Be careful, avoid look-ahead bias
        :return: None
        """
        pass

    @abstractmethod
    def _run(self, history_prices: DataFrame, step: datetime, ) -> TradingSignal:
        """
        Analyse History Data and Predict Next Signal (Current Time)
        :param history_data: HistoryDataExtension
        :return: TradingSignal
        """
        raise NotImplementedError("_analyse_next_signal method must be implemented by subclass")

    @abstractmethod
    def after_all(self) -> None:
        """
        Post run actions after all steps are complete
        :return: None
        """
        pass
