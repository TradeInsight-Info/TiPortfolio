from datetime import datetime, timedelta
from typing import List
from unittest import TestCase

import pandas as pd

from tiportfolio.portfolio.allocation.allocation import (
    PortfolioConfig,
)
from tiportfolio.portfolio.allocation.frequency_based_allocation import FrequencyBasedAllocation, RebalanceFrequency

from tiportfolio.portfolio.trading import Trading
from tiportfolio.portfolio.types import TradingSignal


class DummyStrategy(Trading):
    """Minimal concrete TradingAlgorithm for allocation tests."""

    def run_at_step(self, history_prices, step: datetime) -> TradingSignal:  # type: ignore[override]
        return TradingSignal.EXIT


class DummyFrequencyAllocation(FrequencyBasedAllocation):
    """Concrete subclass used only for testing is_time_to_rebalance."""

    def rebalance(self, current_step: datetime) -> None:  # pragma: no cover - behaviour not under test
        return None


def _build_allocation(freq: RebalanceFrequency) -> DummyFrequencyAllocation:
    # Minimal prices DataFrame – Allocation only uses the index attribute of
    # the first strategy's prices_df.
    dates = pd.to_datetime(["2025-01-01", "2025-01-02"])  # type: ignore[list-item]
    prices = pd.DataFrame(
        {
            "open": [1.0, 1.0],
            "high": [1.0, 1.0],
            "low": [1.0, 1.0],
            "close": [1.0, 1.0],
            "volume": [0, 0],
        },
        index=dates,
    )
    prices.index.name = "date"

    # Pass an empty config dict so that TradingAlgorithm does not attempt to
    # access attributes on ``None``.
    strategy = DummyStrategy("DUMMY", "DUMMY", prices=prices, config={})
    config: PortfolioConfig = {
        "fees_config": {"commission": 0.0, "slippage": 0.0, "risk_free_rate": 0.0},
        "initial_capital": 1_000.0,
        "market_name": "NYSE",
    }

    return DummyFrequencyAllocation(config, [strategy], rebalance_frequency=freq)


def _iterate_days_2025() -> List[datetime]:
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)
    days: List[datetime] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


class TestRebalanceFrequency(TestCase):

    def test_minutely(self) -> None:
        alloc = _build_allocation(RebalanceFrequency.minutely)
        base = datetime(2025, 1, 1, 9, 30, 0)

        # Should rebalance once per minute (at second == 0)
        positives = [
            base + timedelta(minutes=offset) for offset in range(60)
        ]
        for ts in positives:
            self.assertTrue(alloc.is_time_to_rebalance(ts))

        negatives = [
            base.replace(second=sec) for sec in range(1, 60)
        ]
        for ts in negatives:
            self.assertFalse(alloc.is_time_to_rebalance(ts))

    def test_hourly(self) -> None:
        alloc = _build_allocation(RebalanceFrequency.hourly)
        base = datetime(2025, 1, 1, 0, 0, 0)

        positives = [base + timedelta(hours=h) for h in range(24)]
        for ts in positives:
            self.assertTrue(alloc.is_time_to_rebalance(ts))

        negatives = [
            base.replace(minute=15, second=0),
            base.replace(minute=0, second=30),
        ]
        for ts in negatives:
            self.assertFalse(alloc.is_time_to_rebalance(ts))

    def test_daily(self) -> None:
        alloc = _build_allocation(RebalanceFrequency.daily)

        for day in _iterate_days_2025():
            ts_match = day.replace(hour=alloc.rebalance_hour, minute=alloc.rebalance_minute, second=0)
            ts_miss = day.replace(hour=alloc.rebalance_hour, minute=alloc.rebalance_minute, second=1)
            self.assertTrue(alloc.is_time_to_rebalance(ts_match))
            self.assertFalse(alloc.is_time_to_rebalance(ts_miss))

    def test_weekday_frequencies_across_2025(self) -> None:
        mapping = {
            RebalanceFrequency.every_monday: 0,
            RebalanceFrequency.every_tuesday: 1,
            RebalanceFrequency.every_wednesday: 2,
            RebalanceFrequency.every_thursday: 3,
            RebalanceFrequency.every_friday: 4,
        }

        days = _iterate_days_2025()

        for freq, weekday in mapping.items():
            alloc = _build_allocation(freq)
            for day in days:
                ts = day.replace(hour=alloc.rebalance_hour, minute=alloc.rebalance_minute, second=0)
                should_rebalance = day.weekday() == weekday
                self.assertEqual(alloc.is_time_to_rebalance(ts), should_rebalance)

    def test_monthly_frequencies_2025(self) -> None:
        from tiportfolio.utils.get_next_market_datetime import get_next_market_open_day

        # start_of_month and mid_of_month use the *next market open day* from
        # the 1st and 15th of each month respectively; end_of_month uses
        # calendar month end.
        alloc_start = _build_allocation(RebalanceFrequency.start_of_month)
        alloc_mid = _build_allocation(RebalanceFrequency.mid_of_month)
        alloc_end = _build_allocation(RebalanceFrequency.end_of_month)

        for month in range(1, 13):
            # start_of_month
            first_day = datetime(2025, month, 1, alloc_start.rebalance_hour, alloc_start.rebalance_minute, 0)
            first_open = get_next_market_open_day(first_day, alloc_start.market_name)
            ts_start = first_open.to_pydatetime().replace(
                hour=alloc_start.rebalance_hour,
                minute=alloc_start.rebalance_minute,
                second=0,
            )
            self.assertTrue(alloc_start.is_time_to_rebalance(ts_start))

            # mid_of_month (15th)
            mid_day = datetime(2025, month, 15, alloc_mid.rebalance_hour, alloc_mid.rebalance_minute, 0)
            mid_open = get_next_market_open_day(mid_day, alloc_mid.market_name)
            ts_mid = mid_open.to_pydatetime().replace(
                hour=alloc_mid.rebalance_hour,
                minute=alloc_mid.rebalance_minute,
                second=0,
            )
            self.assertTrue(alloc_mid.is_time_to_rebalance(ts_mid))

            # end_of_month – calendar month end
            if month == 12:
                next_month = datetime(2026, 1, 1)
            else:
                next_month = datetime(2025, month + 1, 1)
            end_of_month = (next_month - timedelta(days=1)).replace(
                hour=alloc_end.rebalance_hour,
                minute=alloc_end.rebalance_minute,
                second=0,
            )
            self.assertTrue(alloc_end.is_time_to_rebalance(end_of_month))

    def test_quarterly_frequencies_2025(self) -> None:
        from tiportfolio.utils.get_next_market_datetime import get_next_market_open_day

        alloc_start_q = _build_allocation(RebalanceFrequency.start_of_quarter)
        alloc_mid_q = _build_allocation(RebalanceFrequency.mid_of_quarter)
        alloc_end_q = _build_allocation(RebalanceFrequency.end_of_quarter)

        # Quarters: Q1 (Jan–Mar), Q2 (Apr–Jun), Q3 (Jul–Sep), Q4 (Oct–Dec)
        start_months = [1, 4, 7, 10]
        mid_months = [2, 5, 8, 11]
        end_months = [3, 6, 9, 12]

        # start_of_quarter – use next market open from the 1st of the quarter month
        for m in start_months:
            first_day = datetime(2025, m, 1, alloc_start_q.rebalance_hour, alloc_start_q.rebalance_minute, 0)
            first_open = get_next_market_open_day(first_day, alloc_start_q.market_name)
            ts = first_open.to_pydatetime().replace(
                hour=alloc_start_q.rebalance_hour,
                minute=alloc_start_q.rebalance_minute,
                second=0,
            )
            self.assertTrue(alloc_start_q.is_time_to_rebalance(ts))

        # mid_of_quarter – uses next market open from day 14 of the mid-month
        for m in mid_months:
            mid_day = datetime(2025, m, 14, alloc_mid_q.rebalance_hour, alloc_mid_q.rebalance_minute, 0)
            mid_open = get_next_market_open_day(mid_day, alloc_mid_q.market_name)
            ts = mid_open.to_pydatetime().replace(
                hour=alloc_mid_q.rebalance_hour,
                minute=alloc_mid_q.rebalance_minute,
                second=0,
            )
            self.assertTrue(alloc_mid_q.is_time_to_rebalance(ts))

        # end_of_quarter – calendar month end of 3rd, 6th, 9th, 12th month
        for m in end_months:
            if m == 12:
                next_month = datetime(2026, 1, 1)
            else:
                next_month = datetime(2025, m + 1, 1)
            end_of_month = (next_month - timedelta(days=1)).replace(
                hour=alloc_end_q.rebalance_hour,
                minute=alloc_end_q.rebalance_minute,
                second=0,
            )
            self.assertTrue(alloc_end_q.is_time_to_rebalance(end_of_month))

    def test_yearly_frequencies_2025(self) -> None:
        from tiportfolio.utils.get_next_market_datetime import get_next_market_open_day

        alloc_start_y = _build_allocation(RebalanceFrequency.start_of_year)
        alloc_mid_y = _build_allocation(RebalanceFrequency.mid_of_year)
        alloc_end_y = _build_allocation(RebalanceFrequency.end_of_year)

        # start_of_year – next market open from Jan 1st
        first_day = datetime(2025, 1, 1, alloc_start_y.rebalance_hour, alloc_start_y.rebalance_minute, 0)
        first_open = get_next_market_open_day(first_day, alloc_start_y.market_name)
        ts_start = first_open.to_pydatetime().replace(
            hour=alloc_start_y.rebalance_hour,
            minute=alloc_start_y.rebalance_minute,
            second=0,
        )
        self.assertTrue(alloc_start_y.is_time_to_rebalance(ts_start))

        # mid_of_year – uses July 1st as base
        mid_day = datetime(2025, 7, 1, alloc_mid_y.rebalance_hour, alloc_mid_y.rebalance_minute, 0)
        mid_open = get_next_market_open_day(mid_day, alloc_mid_y.market_name)
        ts_mid = mid_open.to_pydatetime().replace(
            hour=alloc_mid_y.rebalance_hour,
            minute=alloc_mid_y.rebalance_minute,
            second=0,
        )
        self.assertTrue(alloc_mid_y.is_time_to_rebalance(ts_mid))

        # end_of_year – calendar year end
        end_of_year = datetime(2025, 12, 31, alloc_end_y.rebalance_hour, alloc_end_y.rebalance_minute, 0)
        self.assertTrue(alloc_end_y.is_time_to_rebalance(end_of_year))
