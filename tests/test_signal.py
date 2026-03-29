from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from tiportfolio.algo import Context
from tiportfolio.algos.signal import Signal
from tiportfolio.config import TiConfig


def _make_context(date: str) -> Context:
    portfolio = MagicMock()
    portfolio.name = "test"
    return Context(
        portfolio=portfolio,
        prices={},
        date=pd.Timestamp(date, tz="UTC"),
        config=TiConfig(),
    )


class TestSignalScheduleMonthEnd:
    """Signal.Schedule with day='end' fires on last NYSE trading day of each month."""

    def test_fires_on_jan_31_2024(self) -> None:
        # Jan 31, 2024 is a Wednesday — last trading day of Jan
        algo = Signal.Schedule(day="end")
        ctx = _make_context("2024-01-31")
        assert algo(ctx) is True

    def test_skips_mid_month(self) -> None:
        algo = Signal.Schedule(day="end")
        ctx = _make_context("2024-01-15")
        assert algo(ctx) is False

    def test_skips_second_to_last_day(self) -> None:
        algo = Signal.Schedule(day="end")
        ctx = _make_context("2024-01-30")
        assert algo(ctx) is False

    def test_fires_on_feb_29_2024(self) -> None:
        # Feb 29, 2024 is a Thursday — last trading day of Feb in leap year
        algo = Signal.Schedule(day="end")
        ctx = _make_context("2024-02-29")
        assert algo(ctx) is True


class TestSignalMonthly:
    """Signal.Monthly delegates to Schedule and fires once per month."""

    def test_fires_on_month_end(self) -> None:
        algo = Signal.Monthly()
        ctx = _make_context("2024-01-31")
        assert algo(ctx) is True

    def test_skips_non_month_end(self) -> None:
        algo = Signal.Monthly()
        ctx = _make_context("2024-01-15")
        assert algo(ctx) is False

    def test_fires_exactly_once_per_month(self, trading_dates: pd.DatetimeIndex) -> None:
        """Over our fixture data (Jan 2-Feb 1), should fire once (Jan 31)."""
        algo = Signal.Monthly()
        fire_dates = []
        for date in trading_dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        # Our fixture spans Jan 2 to Feb 1 — should fire on Jan 31
        assert len(fire_dates) == 1
        assert fire_dates[0].month == 1
        assert fire_dates[0].day == 31


class TestSignalOnce:
    """Signal.Once fires True on the first call, False thereafter."""

    def test_first_call_true(self) -> None:
        algo = Signal.Once()
        ctx = _make_context("2024-01-02")
        assert algo(ctx) is True

    def test_second_call_false(self) -> None:
        algo = Signal.Once()
        ctx1 = _make_context("2024-01-02")
        algo(ctx1)
        ctx2 = _make_context("2024-01-03")
        assert algo(ctx2) is False

    def test_fires_exactly_once_over_many_bars(self, trading_dates: pd.DatetimeIndex) -> None:
        algo = Signal.Once()
        fire_count = 0
        for date in trading_dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
        assert fire_count == 1
