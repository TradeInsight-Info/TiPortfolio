"""NYSE market calendar util: resolve target dates to closest trading day."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

import pandas as pd


def closest_nyse_trading_day(
    target: date | pd.Timestamp,
    *,
    which: Literal["closest", "on_or_after", "on_or_before"] = "closest",
    max_offset_days: int = 10,
) -> pd.Timestamp | None:
    """Return the NYSE trading day for the given target using expansion rules.

    which:
      - "closest": first in [target, target-1, target+1, target-2, target+2, ...]
      - "on_or_after": first in [target, target+1, target+2, ...]
      - "on_or_before": first in [target, target-1, target-2, ...]

    Returns None if no trading day is found within max_offset_days.
    """
    import pandas_market_calendars as mcal

    if isinstance(target, pd.Timestamp):
        target = target.date()
    elif not isinstance(target, date):
        target = pd.Timestamp(target).date()

    start = target - timedelta(days=max_offset_days)
    end = target + timedelta(days=max_offset_days)
    nyse = mcal.get_calendar("NYSE")
    valid = nyse.valid_days(start_date=start, end_date=end)
    valid_dates = set(d.date() for d in valid)
    # Map date -> one representative timestamp from valid (for return value)
    date_to_ts = {d.date(): d for d in valid}

    def candidates() -> list[date]:
        if which == "closest":
            out: list[date] = [target]
            for i in range(1, max_offset_days + 1):
                out.append(target - timedelta(days=i))
                out.append(target + timedelta(days=i))
            return out
        if which == "on_or_after":
            return [target + timedelta(days=i) for i in range(max_offset_days + 1)]
        if which == "on_or_before":
            return [target - timedelta(days=i) for i in range(max_offset_days + 1)]
        raise ValueError(f"which must be 'closest', 'on_or_after', or 'on_or_before'; got {which!r}")

    for c in candidates():
        if c in valid_dates:
            return date_to_ts[c]
    return None
