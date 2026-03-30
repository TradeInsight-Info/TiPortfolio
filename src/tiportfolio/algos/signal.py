from __future__ import annotations

import calendar

import pandas as pd
import pandas_market_calendars as mcal

from tiportfolio.algo import Algo, Context, Or


class Signal:
    """Namespace for signal algos (when to rebalance)."""

    class Schedule(Algo):
        """Returns True when context.date matches the schedule rule.

        Args:
            day: "start", "mid", "end", or an int (1-31) for a specific day-of-month.
            month: Optional — restrict to a specific month (1-12).
            closest_trading_day: Snap to nearest valid trading day. Default True.
        """

        def __init__(
            self,
            day: int | str = "end",
            month: int | None = None,
            closest_trading_day: bool = True,
        ) -> None:
            self._day = day
            self._month = month
            self._closest_trading_day = closest_trading_day
            self._nyse = mcal.get_calendar("NYSE")

        def __call__(self, context: Context) -> bool:
            date = context.date
            if self._month is not None and date.month != self._month:
                return False
            if self._day == "end":
                return self._is_last_trading_day_of_month(date)
            if self._day == "start":
                return self._matches_target_day(date, 1)
            if self._day == "mid":
                return self._matches_target_day(date, 15)
            if isinstance(self._day, int):
                return self._matches_target_day(date, self._day)
            return False

        def _valid_days_for_month(self, date: pd.Timestamp) -> pd.DatetimeIndex:
            """Get NYSE trading days for the month containing `date`."""
            start = date.replace(day=1)
            end = start + pd.offsets.MonthEnd(0)
            return self._nyse.valid_days(start, end)

        def _matches_target_day(self, date: pd.Timestamp, target_day: int) -> bool:
            """Forward search: fire on the first trading day >= target_day in the month."""
            month_days = calendar.monthrange(date.year, date.month)[1]
            if target_day > month_days:
                return False

            valid_days = self._valid_days_for_month(date)
            if len(valid_days) == 0:
                return False

            target_date = date.replace(day=target_day).normalize()
            if self._closest_trading_day:
                candidates = valid_days[valid_days >= target_date]
                if len(candidates) == 0:
                    return False
                return date.normalize() == candidates[0].normalize()
            else:
                return date.normalize() == target_date and target_date in valid_days.normalize()

        def _is_last_trading_day_of_month(self, date: pd.Timestamp) -> bool:
            """Backward search: fire on the last trading day of the month."""
            valid_days = self._valid_days_for_month(date)
            if len(valid_days) == 0:
                return False
            return date.normalize() == valid_days[-1].normalize()

    class Once(Algo):
        """Fires True on the first call, False on all subsequent calls.

        Use for buy-and-hold strategies: buy once, then hold forever.
        """

        def __init__(self) -> None:
            self._fired = False

        def __call__(self, context: Context) -> bool:
            if self._fired:
                return False
            self._fired = True
            return True

    class Monthly(Algo):
        """Fires on a configured day of each month. Delegates to Schedule."""

        def __init__(self, day: int | str = "end", closest_trading_day: bool = True) -> None:
            self._inner = Signal.Schedule(day=day, closest_trading_day=closest_trading_day)

        def __call__(self, context: Context) -> bool:
            return self._inner(context)

    class Quarterly(Algo):
        """Fires on specified months (default Jan, Apr, Jul, Oct). Delegates to Or(Schedule...).

        Args:
            months: Month numbers (1-12) to fire on. Default [1, 4, 7, 10].
            day: Day parameter passed to each Schedule. Default "end".
        """

        def __init__(
            self,
            months: list[int] | None = None,
            day: int | str = "end",
        ) -> None:
            resolved_months = months if months is not None else [1, 4, 7, 10]
            self._inner = Or(*[Signal.Schedule(month=m, day=day) for m in resolved_months])

        def __call__(self, context: Context) -> bool:
            return self._inner(context)

    class Weekly(Algo):
        """Fires once per ISO week on a configured day.

        Args:
            day: "start" (Monday), "mid" (Wednesday), or "end" (Friday). Default "end".
            closest_trading_day: Snap to nearest valid trading day. Default True.
        """

        _DAY_TARGETS = {"start": 0, "mid": 2, "end": 4}  # Monday=0, Wednesday=2, Friday=4

        def __init__(self, day: str = "end", closest_trading_day: bool = True) -> None:
            self._day = day
            self._closest_trading_day = closest_trading_day
            self._nyse = mcal.get_calendar("NYSE")

        def __call__(self, context: Context) -> bool:
            date = context.date
            target_weekday = self._DAY_TARGETS.get(self._day, 4)

            # Get the ISO week boundaries (Monday to Sunday)
            monday = date - pd.Timedelta(days=date.weekday())
            sunday = monday + pd.Timedelta(days=6)
            valid_days = self._nyse.valid_days(monday, sunday)
            if len(valid_days) == 0:
                return False

            if self._day == "end":
                # Backward search: last trading day of the week
                return date.normalize() == valid_days[-1].normalize()

            # Forward search for "start" and "mid"
            target_date = (monday + pd.Timedelta(days=target_weekday)).normalize()
            if self._closest_trading_day:
                candidates = valid_days[valid_days >= target_date]
                if len(candidates) == 0:
                    return False
                return date.normalize() == candidates[0].normalize()
            else:
                return date.normalize() == target_date and target_date in valid_days.normalize()

    class Yearly(Algo):
        """Fires once per year. Day resolves at year level.

        Args:
            day: "start" (Jan), "mid" (Jul), "end" (Dec), or int (day-of-month).
            month: Override target month. Default derived from day mode.
        """

        _MONTH_TARGETS = {"start": 1, "mid": 7, "end": 12}

        def __init__(
            self,
            day: int | str = "end",
            month: int | None = None,
        ) -> None:
            if month is not None:
                resolved_month = month
            elif isinstance(day, str) and day in self._MONTH_TARGETS:
                resolved_month = self._MONTH_TARGETS[day]
            else:
                resolved_month = 12
            self._inner = Signal.Schedule(month=resolved_month, day=day)

        def __call__(self, context: Context) -> bool:
            return self._inner(context)

    class EveryNPeriods(Algo):
        """Fires every N-th period boundary on a configured day within the period.

        Args:
            n: Fire every N periods.
            period: "day", "week", "month", or "year".
            day: "start", "mid", "end" — which day within the period. Default "end".
        """

        def __init__(
            self,
            n: int,
            period: str,
            day: str = "end",
        ) -> None:
            self._n = n
            self._period = period
            self._day = day
            self._counter = n - 1  # fire on first eligible period
            self._last_period_key: int | tuple[int, int] | None = None
            self._nyse = mcal.get_calendar("NYSE")

        def __call__(self, context: Context) -> bool:
            date = context.date
            period_key = self._get_period_key(date)

            if self._period == "day":
                # Every N-th trading day
                self._counter += 1
                if self._counter >= self._n:
                    self._counter = 0
                    return True
                return False

            # For week/month/year: detect period boundary
            if period_key != self._last_period_key:
                self._counter += 1
                self._last_period_key = period_key

            if self._counter >= self._n:
                fired = self._is_target_day(date)
                if fired:
                    self._counter = 0
                return fired

            return False

        def _get_period_key(self, date: pd.Timestamp) -> int | tuple[int, int]:
            if self._period == "week":
                iso = date.isocalendar()
                return (iso[0], iso[1])  # (year, week)
            if self._period == "month":
                return (date.year, date.month)
            if self._period == "year":
                return date.year
            return 0  # "day" — not used for boundary detection

        def _is_target_day(self, date: pd.Timestamp) -> bool:
            """Check if date is the target day within its period."""
            if self._period == "week":
                weekly = Signal.Weekly(day=self._day)
                return weekly(Context(
                    portfolio=None, prices={}, date=date,  # type: ignore[arg-type]
                    config=None,  # type: ignore[arg-type]
                ))
            if self._period == "month":
                schedule = Signal.Schedule(day=self._day)
                return schedule(Context(
                    portfolio=None, prices={}, date=date,  # type: ignore[arg-type]
                    config=None,  # type: ignore[arg-type]
                ))
            if self._period == "year":
                yearly = Signal.Yearly(day=self._day)
                return yearly(Context(
                    portfolio=None, prices={}, date=date,  # type: ignore[arg-type]
                    config=None,  # type: ignore[arg-type]
                ))
            return True  # "day" period — always the target day

    class VIX(Algo):
        """Regime switching based on VIX level with hysteresis.

        Writes to both context.selected and context.weights:
        - VIX < low → children[0] (low-vol / risk-on)
        - VIX > high → children[1] (high-vol / risk-off)
        - Between thresholds → previous selection persists

        Args:
            high: Upper VIX threshold.
            low: Lower VIX threshold.
            data: Dict containing "^VIX" DataFrame with close prices.
        """

        def __init__(
            self,
            high: float,
            low: float,
            data: dict[str, pd.DataFrame],
        ) -> None:
            self._high = high
            self._low = low
            self._data = data
            self._active: object | None = None  # Portfolio, lazily initialised

        def __call__(self, context: Context) -> bool:
            if self._active is None:
                self._active = context.portfolio.children[0]

            vix_now = self._data["^VIX"].loc[context.date, "close"]
            if vix_now > self._high:
                self._active = context.portfolio.children[1]
            elif vix_now < self._low:
                self._active = context.portfolio.children[0]
            # else: between thresholds — hysteresis, keep previous

            context.selected = [self._active]
            context.weights = {self._active.name: 1.0}  # type: ignore[union-attr]
            return True
