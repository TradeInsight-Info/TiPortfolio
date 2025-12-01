from abc import ABC
from datetime import datetime, timedelta
from enum import Enum
from typing import List

from .allocation import Allocation, PortfolioConfig
from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from tiportfolio.utils.get_next_market_datetime import get_next_market_open_day


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
