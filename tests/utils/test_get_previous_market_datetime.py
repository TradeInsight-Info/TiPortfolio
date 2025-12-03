from unittest import TestCase

from datetime import datetime

import pandas as pd

from tiportfolio.utils.get_previous_market_datetime import get_previous_market_open_day


class TestGetPreviousMarketOpenDay(TestCase):

    def test_previous_open_on_regular_trading_day_naive_datetime(self) -> None:
        """Naive datetimes during trading hours return prior day's open.

        For a midday timestamp on a regular trading day (2024-01-03,
        Wednesday), the helper currently returns the last market open strictly
        before ``dt``, which corresponds to the previous trading day's open
        (2024-01-02).
        """

        dt = datetime(2024, 1, 3, 12, 0, 0)

        prev_open = get_previous_market_open_day(dt, "NYSE")

        self.assertEqual(prev_open.date(), pd.Timestamp("2024-01-02").date())

    def test_previous_open_before_open_moves_to_prior_trading_day(self) -> None:
        """Timestamp before today's open should give previous trading day's open."""

        # 2024-01-03 is a Wednesday trading day. A very early timestamp that
        # is still before the session open should resolve to Tuesday 2024-01-02.
        dt = datetime(2024, 1, 3, 0, 5, 0)

        prev_open = get_previous_market_open_day(dt, "NYSE")

        self.assertEqual(prev_open.date(), pd.Timestamp("2024-01-02").date())

    def test_previous_open_skips_weekend(self) -> None:
        """Weekend date should return the previous Friday open."""

        # Sunday, 2024-01-07 – NYSE closed. Previous open is Friday 2024-01-05.
        dt = datetime(2024, 1, 7, 12, 0, 0)

        prev_open = get_previous_market_open_day(dt, "NYSE")

        self.assertEqual(prev_open.date(), pd.Timestamp("2024-01-05").date())

    def test_previous_open_timezone_awareness(self) -> None:
        """Returned timestamp should be timezone-aware in market tz."""

        dt = datetime(2024, 1, 3, 12, 0, 0)

        prev_open = get_previous_market_open_day(dt, "NYSE")

        self.assertIsNotNone(prev_open.tzinfo)
