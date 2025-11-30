import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, TypedDict, Optional

from datetime import datetime, timedelta

from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.utils.get_next_market_datetime import get_next_market_open_day
from tiportfolio.utils.init_tz import init_tz

init_tz()  # todo move to main entry point


class RebalanceFrequency(Enum):
    minutely = 'minutely'
    hourly = 'hourly'
    daily = 'daily'
    every_monday = 'every_monday'
    every_tuesday = 'every_tuesday'
    every_wednesday = 'every_wednesday'
    every_thursday = 'every_thursday'
    every_friday = 'every_friday'
    start_of_month = 'start_of_month'
    mid_of_month = 'mid_of_month'
    end_of_month = 'end_of_month'
    start_of_quarter = 'start_of_quarter'
    mid_of_quarter = 'mid_of_quarter'
    end_of_quarter = 'end_of_quarter'
    start_of_year = 'start_of_year'
    mid_of_year = 'mid_of_year'
    end_of_year = 'end_of_year'


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


class FrequencyBasedAllocation(Allocation, ABC):

    def __init__(
            self,
            config: PortfolioConfig,
            strategies: List[TradingAlgorithm],
            rebalance_frequency: RebalanceFrequency,
            market_name: str = 'NYSE',
            hour: int = 9,
            minute: int = 30,
    ) -> None:
        super().__init__(config, strategies)
        self.rebalance_frequency = rebalance_frequency
        self.market_name = market_name
        self.rebalance_hour = hour
        self.rebalance_minute = minute
        self.rebalance_second = 0

    def is_time_to_rebalance(self, current_step: datetime) -> bool:
        
        def matches_time(ts: datetime) -> bool:
            return ts.hour == self.rebalance_hour and ts.minute == self.rebalance_minute and ts.second == 0

        if self.rebalance_frequency == RebalanceFrequency.minutely:
            return current_step.second == 0
        elif self.rebalance_frequency == RebalanceFrequency.hourly:
            return current_step.minute == 0 and current_step.second == 0
        elif self.rebalance_frequency == RebalanceFrequency.daily:
            return matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.every_monday:
            return current_step.weekday() == 0 and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.every_tuesday:
            return current_step.weekday() == 1 and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.every_wednesday:
            return current_step.weekday() == 2 and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.every_thursday:
            return current_step.weekday() == 3 and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.every_friday:
            return current_step.weekday() == 4 and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.start_of_month:
            first_day = current_step.replace(day=1)
            closest_open = get_next_market_open_day(first_day, self.market_name)
            return current_step.date() == closest_open.date() and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.mid_of_month:
            mid_day = current_step.replace(day=15)
            closest_open = get_next_market_open_day(mid_day, self.market_name)
            return current_step.date() == closest_open.date() and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.end_of_month:
            # approximate by calendar month end
            first_next_month = (current_step.replace(day=28) + timedelta(days=4)).replace(day=1)
            day_in_end = first_next_month - timedelta(days=1)
            # use calendar month end check (may differ from last trading day)
            return current_step.date() == day_in_end.date() and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.start_of_quarter:
            day_in_beginning = current_step.replace(day=1)
            if current_step.month in (1, 4, 7, 10):
                closest_open = get_next_market_open_day(day_in_beginning, self.market_name)
                return current_step.date() == closest_open.date() and matches_time(current_step)
            return False
        elif self.rebalance_frequency == RebalanceFrequency.mid_of_quarter:

            day_in_middle = current_step.replace(day=14)
            if current_step.month in (2, 5, 8, 11):
                closest_open = get_next_market_open_day(day_in_middle, self.market_name)
                return current_step.date() == closest_open.date() and matches_time(current_step)
            return False


            return current_step.month in (2, 5, 8, 11) and current_step.day == 15 and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.end_of_quarter:
            # end of quarter months: 3, 6, 9, 12
            first_next_month = (current_step.replace(day=28) + timedelta(days=4)).replace(day=1)
            day_in_end = first_next_month - timedelta(days=1)
            return current_step.month in (3, 6, 9,
                                          12) and current_step.date() == day_in_end.date() and matches_time(
                current_step)
        elif self.rebalance_frequency == RebalanceFrequency.start_of_year:
            first_day = current_step.replace(month=1, day=1)
            closest_open = get_next_market_open_day(first_day, self.market_name)
            return current_step.date() == closest_open.date() and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.mid_of_year:
            # use July 1 as mid-year
            mid_year = current_step.replace(month=7, day=1)
            closest_open = get_next_market_open_day(mid_year, self.market_name)
            return current_step.date() == closest_open.date() and matches_time(current_step)
        elif self.rebalance_frequency == RebalanceFrequency.end_of_year:
            first_next_year = current_step.replace(month=12, day=28) + timedelta(days=4)
            first_of_next_year = first_next_year.replace(month=1, day=1)
            day_in_end = first_of_next_year - timedelta(days=1)
            return current_step.date() == day_in_end.date() and matches_time(current_step)

        return False
