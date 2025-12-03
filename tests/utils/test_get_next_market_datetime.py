from unittest import TestCase

from datetime import datetime

import pandas as pd

from tiportfolio.utils.get_next_market_datetime import get_next_market_open_day


class TestGetNextMarketOpenDay(TestCase):

    def test_next_open_on_regular_trading_day_naive_datetime(self) -> None:
        """Naive datetimes during trading hours should return same-day open.

        We pick a known NYSE trading day (2024-01-03, Wednesday) and a midday
        timestamp. The helper should return the market open for that day.
        """

        dt = datetime(2024, 1, 3, 12, 0, 0)

        next_open = get_next_market_open_day(dt, "NYSE")

        # 2024-01-03 is a regular trading day; we expect the open of that
        # session. Timezone is whatever pandas-market-calendars uses for NYSE
        # (typically US/Eastern).
        self.assertEqual(next_open.date(), pd.Timestamp("2024-01-03").date())

    def test_next_open_after_close_moves_to_next_trading_day(self) -> None:
        """After-hours timestamp should move to the *next* trading session.

        We use a late-evening timestamp on a regular trading day and expect
        the function to return the open of the following trading day.
        """

        dt = datetime(2024, 1, 3, 23, 0, 0)

        next_open = get_next_market_open_day(dt, "NYSE")

        self.assertEqual(next_open.date(), pd.Timestamp("2024-01-04").date())

    def test_next_open_skips_weekend(self) -> None:
        """A weekend date should skip to the following Monday open."""

        # Saturday, 2024-01-06 – NYSE is closed
        dt = datetime(2024, 1, 6, 12, 0, 0)

        next_open = get_next_market_open_day(dt, "NYSE")

        # First trading day after this Saturday is Monday 2024-01-08.
        self.assertEqual(next_open.date(), pd.Timestamp("2024-01-08").date())

    def test_next_open_timezone_awareness(self) -> None:
        """Returned timestamp should be timezone-aware in market tz."""

        dt = datetime(2024, 1, 3, 12, 0, 0)

        next_open = get_next_market_open_day(dt, "NYSE")

        self.assertIsNotNone(next_open.tzinfo)
