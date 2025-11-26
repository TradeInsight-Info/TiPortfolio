from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, Union

from .types import HistoryDataExtension


class Strategy(ABC, Generic[HistoryDataExtension]):

    def __init__(self, name) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"Strategy({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)

    @abstractmethod
    def analyse_next_signal(self, history_data: HistoryDataExtension | dict) -> Union[1, 0, -1]:
        """
        Analyse History Data and Predict Next Signal (Current Time)
        :param history_data: HistoryDataExtension
        :return: 1, 0, -1
        """
        pass

    def execute(self, all_data: HistoryDataExtension, step: datetime) -> Union[1, 0, -1]:
        """
        Generate trading signals using the strategy function
        :param step: datetime
        :param all_data: HistoryDataExtension
        :return: 1 or 0 or -1 (1 long, 0 exit, -1 short)
        """

        history_data = {key: value.loc[:step] for key, value in all_data.items()}
        return self.analyse_next_signal(history_data)
