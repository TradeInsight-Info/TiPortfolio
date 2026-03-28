from __future__ import annotations

import pandas as pd
import pandas_market_calendars as mcal

from tiportfolio.algo import Algo, Context


class Signal:
    """Namespace for signal algos (when to rebalance)."""

    class Schedule(Algo):
        """Returns True when context.date matches the schedule rule.

        Args:
            day: "end" for last trading day of the month, or an int for a specific day.
            month: Optional — restrict to a specific month (1-12).
            next_trading_day: If the target day is not a trading day, use the next one.
        """

        def __init__(
            self,
            day: int | str = "end",
            month: int | None = None,
            next_trading_day: bool = True,
        ) -> None:
            self._day = day
            self._month = month
            self._next_trading_day = next_trading_day
            self._nyse = mcal.get_calendar("NYSE")

        def __call__(self, context: Context) -> bool:
            date = context.date
            if self._month is not None and date.month != self._month:
                return False
            if self._day == "end":
                return self._is_last_trading_day_of_month(date)
            return False  # int day support deferred to Chunk 2

        def _is_last_trading_day_of_month(self, date: pd.Timestamp) -> bool:
            start = date.replace(day=1)
            # Go to end of month
            end = start + pd.offsets.MonthEnd(0)
            schedule = self._nyse.valid_days(start, end)
            if len(schedule) == 0:
                return False
            last_trading_day = schedule[-1]
            # Compare date-only (both should be UTC)
            return date.normalize() == last_trading_day.normalize()

    class Monthly(Algo):
        """Fires on the last trading day of each month. Delegates to Schedule."""

        def __init__(self, day: int | str = "end", next_trading_day: bool = True) -> None:
            self._inner = Signal.Schedule(day=day, next_trading_day=next_trading_day)

        def __call__(self, context: Context) -> bool:
            return self._inner(context)
