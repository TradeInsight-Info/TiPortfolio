"""Rebalance calendar: produce rebalance dates from schedule aligned to trading days."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from tiportfolio.market_calendar import closest_nyse_trading_day

VALID_SCHEDULES = (
    "month_end",
    "month_mid",
    "month_start",
    "never",
    "quarter_end",
    "quarter_mid",
    "quarter_start",
    "vix_regime",
    "weekly_friday",
    "weekly_monday",
    "weekly_wednesday",
    "year_end",
    "year_mid",
    "year_start",
)


def _target_dates_month_mid(first_ts: pd.Timestamp, last_ts: pd.Timestamp) -> pd.DatetimeIndex:
    """15th of each month in range."""
    tz = first_ts.tz
    dates: list[pd.Timestamp] = []
    y, m = first_ts.year, first_ts.month
    end_y, end_m = last_ts.year, last_ts.month
    while (y, m) <= (end_y, end_m):
        d = pd.Timestamp(year=y, month=m, day=15, tz=tz)
        if first_ts <= d <= last_ts:
            dates.append(d)
        m += 1
        if m > 12:
            m = 1
            y += 1
    return pd.DatetimeIndex(dates) if dates else pd.DatetimeIndex([])


def _target_dates_quarter_mid(first_ts: pd.Timestamp, last_ts: pd.Timestamp) -> pd.DatetimeIndex:
    """15th of 2nd month of each quarter: Feb 15, May 15, Aug 15, Nov 15."""
    tz = first_ts.tz
    dates: list[pd.Timestamp] = []
    for y in range(first_ts.year, last_ts.year + 1):
        for month in (2, 5, 8, 11):
            d = pd.Timestamp(year=y, month=month, day=15, tz=tz)
            if first_ts <= d <= last_ts:
                dates.append(d)
    return pd.DatetimeIndex(dates).unique().sort_values() if dates else pd.DatetimeIndex([])


def _target_dates_year_mid(first_ts: pd.Timestamp, last_ts: pd.Timestamp) -> pd.DatetimeIndex:
    """July 1 each year."""
    tz = first_ts.tz
    dates = [
        pd.Timestamp(year=y, month=7, day=1, tz=tz)
        for y in range(first_ts.year, last_ts.year + 1)
        if first_ts <= pd.Timestamp(year=y, month=7, day=1, tz=tz) <= last_ts
    ]
    return pd.DatetimeIndex(dates) if dates else pd.DatetimeIndex([])


def _vix_regime_rebalance_dates(
    trading_dates: pd.DatetimeIndex,
    vix_series: pd.Series,
    target_vix: float,
    lower_bound: float,
    upper_bound: float,
    signal_delay: int = 1,
) -> list[pd.Timestamp]:
    """Return rebalance dates when VIX crosses above (target+upper) or below (target+lower).
    
    When signal_delay > 0, the execution date is shifted forward by signal_delay trading days
    from the signal (crossing) date. Dates that fall outside trading_dates are discarded.
    """
    vix_aligned = vix_series.reindex(trading_dates).ffill().bfill()
    upper_thresh = target_vix + upper_bound
    lower_thresh = target_vix + lower_bound
    
    # Collect signal dates (where crossings occur)
    signal_dates_indices: list[int] = []
    for i, date in enumerate(trading_dates):
        v = vix_aligned.loc[date]
        if pd.isna(v):
            continue
        if i == 0:
            prev_v = v
            continue
        prev_v = vix_aligned.loc[trading_dates[i - 1]]
        if pd.isna(prev_v):
            continue
        # Cross above upper: prev < upper_thresh and now >= upper_thresh
        if prev_v < upper_thresh and v >= upper_thresh:
            signal_dates_indices.append(i)
        # Cross below lower: prev > lower_thresh and now <= lower_thresh
        if prev_v > lower_thresh and v <= lower_thresh:
            signal_dates_indices.append(i)
    
    # Shift each signal date by signal_delay trading days forward
    # Discard dates that fall outside the trading_dates range
    rebalance_list: list[pd.Timestamp] = []
    max_idx = len(trading_dates) - 1
    seen_execution_dates: set[pd.Timestamp] = set()
    
    for signal_idx in signal_dates_indices:
        execution_idx = signal_idx + signal_delay
        if execution_idx > max_idx:
            # Signal on last trading day(s) - execution date falls outside range, discard
            continue
        execution_date = trading_dates[execution_idx]
        # Deduplicate: consecutive crossings may map to same execution day
        if execution_date not in seen_execution_dates:
            rebalance_list.append(execution_date)
            seen_execution_dates.add(execution_date)
    
    return rebalance_list


def get_rebalance_dates(
    trading_dates: pd.DatetimeIndex,
    schedule: str,
    *,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
    vix_series: pd.Series | None = None,
    target_vix: float | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    signal_delay: int = 1,
    **kwargs: Any,
) -> pd.DatetimeIndex:
    """Return rebalance dates aligned to trading_dates for the given schedule.

    Uses NYSE calendar to resolve each target to a market day; only dates
    present in trading_dates are included.
    For schedule "vix_regime", vix_series, target_vix, lower_bound, upper_bound are required.
    """
    # Extract vix_series and other parameters from kwargs if not provided directly
    if vix_series is None and "vix_series" in kwargs:
        vix_series = kwargs["vix_series"]
    if target_vix is None and "target_vix" in kwargs:
        target_vix = kwargs["target_vix"]
    if lower_bound is None and "lower_bound" in kwargs:
        lower_bound = kwargs["lower_bound"]
    if upper_bound is None and "upper_bound" in kwargs:
        upper_bound = kwargs["upper_bound"]
    if not isinstance(trading_dates, pd.DatetimeIndex):
        trading_dates = pd.DatetimeIndex(trading_dates)
    if start is not None:
        start = pd.Timestamp(start)
        # Ensure timezone compatibility: if trading_dates has timezone, convert start to UTC
        if hasattr(trading_dates, 'tz') and trading_dates.tz is not None:
            start = start.tz_localize(trading_dates.tz) if start.tz is None else start
        trading_dates = trading_dates[trading_dates >= start]
    if end is not None:
        end = pd.Timestamp(end)
        # Ensure timezone compatibility: if trading_dates has timezone, convert end to UTC
        if hasattr(trading_dates, 'tz') and trading_dates.tz is not None:
            end = end.tz_localize(trading_dates.tz) if end.tz is None else end
        trading_dates = trading_dates[trading_dates <= end]
    if len(trading_dates) == 0:
        return pd.DatetimeIndex([])

    first_ts = trading_dates.min()
    last_ts = trading_dates.max()

    if schedule == "month_end":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="ME")
        which = "on_or_before"
    elif schedule == "month_start":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="MS")
        which = "on_or_after"
    elif schedule == "quarter_end":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="QE")
        which = "on_or_before"
    elif schedule == "quarter_start":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="QS")
        which = "on_or_after"
    elif schedule == "year_end":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="YE")
        which = "on_or_before"
    elif schedule == "year_start":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="YS")
        which = "on_or_after"
    elif schedule == "month_mid":
        target_dates = _target_dates_month_mid(first_ts, last_ts)
        which = "closest"
    elif schedule == "quarter_mid":
        target_dates = _target_dates_quarter_mid(first_ts, last_ts)
        which = "closest"
    elif schedule == "year_mid":
        target_dates = _target_dates_year_mid(first_ts, last_ts)
        which = "closest"
    elif schedule == "weekly_monday":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="W-MON")
        which = "on_or_after"
    elif schedule == "weekly_wednesday":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="W-WED")
        which = "on_or_after"
    elif schedule == "weekly_friday":
        target_dates = pd.date_range(start=first_ts, end=last_ts, freq="W-FRI")
        which = "on_or_after"
    elif schedule == "vix_regime":
        if vix_series is None or target_vix is None or lower_bound is None or upper_bound is None:
            raise ValueError(
                "schedule 'vix_regime' requires vix_series, target_vix, lower_bound, upper_bound"
            )
        rebalance_list = _vix_regime_rebalance_dates(
            trading_dates, vix_series, target_vix, lower_bound, upper_bound,
            signal_delay=signal_delay,
        )
        return pd.DatetimeIndex(rebalance_list).unique().sort_values()
    elif schedule == "never":
        return pd.DatetimeIndex([])
    else:
        raise ValueError(
            f"Unknown schedule {schedule!r}; use one of {list(VALID_SCHEDULES)}"
        )

    trading_dates_by_date: dict[date, pd.Timestamp] = {
        pd.Timestamp(t).date(): t for t in trading_dates
    }
    rebalance_list: list[pd.Timestamp] = []

    on_or_before = which == "on_or_before"
    for t in target_dates:
        resolved = closest_nyse_trading_day(t, which=which)
        if resolved is not None:
            r_date = resolved.date()
            if r_date in trading_dates_by_date:
                rebalance_list.append(trading_dates_by_date[r_date])
                continue
        # Fallback: resolved missing or not in data (e.g. non-NYSE data); use nearest in trading_dates
        if on_or_before:
            on_or_before_dates = trading_dates[trading_dates <= t]
            if len(on_or_before_dates) > 0:
                rebalance_list.append(on_or_before_dates[-1])
        else:
            on_or_after = trading_dates[trading_dates >= t]
            if len(on_or_after) > 0:
                rebalance_list.append(on_or_after[0])
    return pd.DatetimeIndex(rebalance_list).unique().sort_values()


def normalize_price_index(df: pd.DataFrame, tz: str = 'UTC') -> pd.DataFrame:
    """Normalize DataFrame index to timezone-aware datetime with specified timezone.
    
    - If index is not DatetimeIndex, convert it
    - If index has no timezone, check for mixed tz and handle accordingly
    - If index has timezone, convert to specified tz
    - Set index name to 'date'
    """
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        # Check if it's actually mixed timezones (tz=None but individual elements have tz)
        if len(df.index) > 0 and df.index[0].tz is not None:
            # Mixed timezones, convert to target tz
            df.index = df.index.tz_convert(tz)
        else:
            # Truly naive, localize to target tz
            df.index = df.index.tz_localize(tz)
    else:
        # Has uniform timezone, convert to target tz
        df.index = df.index.tz_convert(tz)
    df.index.name = "date"
    return df


class Schedule:
    """Rebalance schedule spec; all dates are resolved to NYSE trading days."""

    def __init__(self, spec: str) -> None:
        if spec not in VALID_SCHEDULES:
            raise ValueError(
                f"schedule must be one of {list(VALID_SCHEDULES)}; got {spec!r}"
            )
        self.spec = spec
