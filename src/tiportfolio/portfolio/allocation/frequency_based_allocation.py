from abc import ABC
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Set

from pandas import Timestamp

from .allocation import Allocation, PortfolioConfig
from tiportfolio.portfolio.trading import Trading
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
            strategies: List[Trading],
            rebalance_frequency: RebalanceFrequency,
            hour: int = 9,
            minute: int = 30,
    ) -> None:
        super().__init__(config, strategies)
        self.rebalance_frequency = rebalance_frequency
        self.market_name = self.config.get("market_name", 'NYSE')
        self.rebalance_hour = hour
        self.rebalance_minute = minute
        self.rebalance_second = 0
        # Pre-compute rebalance dates for market-dependent frequencies
        # to optimize performance
        self._rebalance_dates: Set[datetime.date] = set()
        self._precompute_rebalance_dates()

    def _precompute_rebalance_dates(self) -> None:
        """Pre-compute all rebalance dates for market-dependent frequencies.

        This optimization avoids calling get_next_market_open_day() for
        every step in walk_forward(), which can be very slow for large
        datasets.
        """
        # Only pre-compute for frequencies that depend on market calendar
        market_dependent_freqs = {
            RebalanceFrequency.start_of_month,
            RebalanceFrequency.mid_of_month,
            RebalanceFrequency.start_of_quarter,
            RebalanceFrequency.mid_of_quarter,
            RebalanceFrequency.start_of_year,
            RebalanceFrequency.mid_of_year,
        }

        if self.rebalance_frequency not in market_dependent_freqs:
            return

        if self.all_steps.empty:
            return

        # Get date range from all_steps
        start_date = self.all_steps[0].date()
        end_date = self.all_steps[-1].date()

        # Generate candidate dates based on frequency
        candidate_dates = []

        if self.rebalance_frequency == RebalanceFrequency.start_of_month:
            # First of each month in range
            current = datetime(start_date.year, start_date.month, 1)
            while current.date() <= end_date:
                candidate_dates.append(current)
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        elif self.rebalance_frequency == RebalanceFrequency.mid_of_month:
            # 15th of each month in range
            current = datetime(start_date.year, start_date.month, 15)
            while current.date() <= end_date:
                candidate_dates.append(current)
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=15)
                else:
                    current = current.replace(month=current.month + 1, day=15)

        elif self.rebalance_frequency == RebalanceFrequency.start_of_quarter:
            # First of quarter months (Jan, Apr, Jul, Oct)
            quarter_months = [1, 4, 7, 10]
            current = datetime(start_date.year, start_date.month, 1)
            # Move to next quarter start
            while current.month not in quarter_months:
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            while current.date() <= end_date:
                candidate_dates.append(current)
                if current.month == 10:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 3)

        elif self.rebalance_frequency == RebalanceFrequency.mid_of_quarter:
            # 14th of mid-quarter months (Feb, May, Aug, Nov)
            quarter_mid_months = [2, 5, 8, 11]
            current = datetime(start_date.year, start_date.month, 14)
            # Move to next quarter mid
            while current.month not in quarter_mid_months:
                if current.month == 12:
                    current = current.replace(
                        year=current.year + 1, month=2, day=14
                    )
                elif current.month < 2:
                    current = current.replace(month=2, day=14)
                elif current.month < 5:
                    current = current.replace(month=5, day=14)
                elif current.month < 8:
                    current = current.replace(month=8, day=14)
                else:
                    current = current.replace(month=11, day=14)
            while current.date() <= end_date:
                candidate_dates.append(current)
                if current.month == 11:
                    current = current.replace(
                        year=current.year + 1, month=2, day=14
                    )
                elif current.month == 2:
                    current = current.replace(month=5, day=14)
                elif current.month == 5:
                    current = current.replace(month=8, day=14)
                else:  # month == 8
                    current = current.replace(month=11, day=14)

        elif self.rebalance_frequency == RebalanceFrequency.start_of_year:
            # January 1st
            current = datetime(start_date.year, 1, 1)
            while current.date() <= end_date:
                candidate_dates.append(current)
                current = current.replace(year=current.year + 1)

        elif self.rebalance_frequency == RebalanceFrequency.mid_of_year:
            # July 1st
            current = datetime(start_date.year, 7, 1)
            if current.date() < start_date:
                current = current.replace(year=current.year + 1)
            while current.date() <= end_date:
                candidate_dates.append(current)
                current = current.replace(year=current.year + 1)

        # Convert candidate dates to market open days and store
        for candidate in candidate_dates:
            try:
                market_open = get_next_market_open_day(
                    candidate, self.market_name
                )
                # Store just the date part for fast lookup
                self._rebalance_dates.add(market_open.date())
            except ValueError:
                # Skip if no market open found
                continue

    def is_time_to_rebalance(self, current_step: Timestamp) -> bool:
        # Handle both pandas Timestamp and plain datetime objects
        if isinstance(current_step, datetime):
            dt = current_step
        else:
            dt = current_step.to_pydatetime()

        def matches_time(ts: datetime) -> bool:
            return ts.hour == self.rebalance_hour and ts.minute == self.rebalance_minute and ts.second == 0

        if self.rebalance_frequency == RebalanceFrequency.minutely:
            return dt.second == 0
        elif self.rebalance_frequency == RebalanceFrequency.hourly:
            return dt.minute == 0 and dt.second == 0
        elif self.rebalance_frequency == RebalanceFrequency.daily:
            return matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.every_monday:
            return dt.weekday() == 0 and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.every_tuesday:
            return dt.weekday() == 1 and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.every_wednesday:
            return dt.weekday() == 2 and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.every_thursday:
            return dt.weekday() == 3 and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.every_friday:
            return dt.weekday() == 4 and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.start_of_month:
            # Use pre-computed dates for fast lookup; if the queried date is
            # outside the precomputed range (e.g. unit tests), fall back to
            # computing the next market open day for the 1st of the month.
            if dt.date() in self._rebalance_dates:
                return matches_time(dt)
            # Fallback dynamic check
            try:
                candidate = datetime(dt.year, dt.month, 1)
                market_open = get_next_market_open_day(candidate, self.market_name)
                return market_open.date() == dt.date() and matches_time(dt)
            except ValueError:
                return False
        elif self.rebalance_frequency == RebalanceFrequency.mid_of_month:
            # Use pre-computed dates for fast lookup; if not present compute
            # from the 15th of the month.
            if dt.date() in self._rebalance_dates:
                return matches_time(dt)
            try:
                candidate = datetime(dt.year, dt.month, 15)
                market_open = get_next_market_open_day(candidate, self.market_name)
                return market_open.date() == dt.date() and matches_time(dt)
            except ValueError:
                return False
        elif self.rebalance_frequency == RebalanceFrequency.end_of_month:
            # approximate by calendar month end
            first_next_month = (dt.replace(day=28) + timedelta(days=4)).replace(day=1)
            day_in_end = first_next_month - timedelta(days=1)
            # use calendar month end check (may differ from last trading day)
            return dt.date() == day_in_end.date() and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.start_of_quarter:
            # Use pre-computed dates for fast lookup; fall back to computing
            # next market open from the 1st of the quarter month.
            if dt.month not in (1, 4, 7, 10):
                return False
            if dt.date() in self._rebalance_dates:
                return matches_time(dt)
            try:
                candidate = datetime(dt.year, dt.month, 1)
                market_open = get_next_market_open_day(candidate, self.market_name)
                return market_open.date() == dt.date() and matches_time(dt)
            except ValueError:
                return False
        elif self.rebalance_frequency == RebalanceFrequency.mid_of_quarter:
            # Use pre-computed dates for fast lookup; fallback to computing
            # next market open from day 14 of the mid-quarter month.
            if dt.month not in (2, 5, 8, 11):
                return False
            if dt.date() in self._rebalance_dates:
                return matches_time(dt)
            try:
                candidate = datetime(dt.year, dt.month, 14)
                market_open = get_next_market_open_day(candidate, self.market_name)
                return market_open.date() == dt.date() and matches_time(dt)
            except ValueError:
                return False
        elif self.rebalance_frequency == RebalanceFrequency.start_of_year:
            # Use pre-computed dates for fast lookup; fallback to Jan 1st
            if dt.date() in self._rebalance_dates:
                return matches_time(dt)
            try:
                candidate = datetime(dt.year, 1, 1)
                market_open = get_next_market_open_day(candidate, self.market_name)
                return market_open.date() == dt.date() and matches_time(dt)
            except ValueError:
                return False
        elif self.rebalance_frequency == RebalanceFrequency.mid_of_year:
            # Use pre-computed dates for fast lookup; fallback to Jul 1st
            if dt.date() in self._rebalance_dates:
                return matches_time(dt)
            try:
                candidate = datetime(dt.year, 7, 1)
                market_open = get_next_market_open_day(candidate, self.market_name)
                return market_open.date() == dt.date() and matches_time(dt)
            except ValueError:
                return False
        elif self.rebalance_frequency == RebalanceFrequency.end_of_quarter:
            # Check if current month is the end of a quarter (Mar, Jun, Sep, Dec)
            if dt.month not in (3, 6, 9, 12):
                return False
            # Calculate last day of current month
            if dt.month == 12:
                first_next_month = datetime(dt.year + 1, 1, 1)
            else:
                first_next_month = datetime(dt.year, dt.month + 1, 1)
            day_in_end = first_next_month - timedelta(days=1)
            return dt.date() == day_in_end.date() and matches_time(dt)
        elif self.rebalance_frequency == RebalanceFrequency.end_of_year:
            first_next_year = dt.replace(month=12, day=28) + timedelta(days=4)
            first_of_next_year = first_next_year.replace(month=1, day=1)
            day_in_end = first_of_next_year - timedelta(days=1)
            return dt.date() == day_in_end.date() and matches_time(dt)

        return False
