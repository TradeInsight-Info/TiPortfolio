"""Tests for NYSE market calendar util."""

from datetime import date

import pandas as pd
import pytest

from tiportfolio.market_calendar import closest_nyse_trading_day


def test_closest_nyse_trading_day_symmetric_expansion():
    """July 4 is holiday; closest is July 3 or July 5 (symmetric expansion)."""
    # 2019-07-04 is Thursday, US Independence Day
    result = closest_nyse_trading_day(date(2019, 7, 4), which="closest")
    assert result is not None
    assert result.date() in (date(2019, 7, 3), date(2019, 7, 5))


def test_closest_nyse_trading_day_weekend():
    """Saturday expands to Friday or Monday."""
    result = closest_nyse_trading_day(date(2019, 6, 15), which="closest")  # Saturday
    assert result is not None
    assert result.date() in (date(2019, 6, 14), date(2019, 6, 17))


def test_closest_nyse_trading_day_on_or_after():
    """Jan 1 is closed; on_or_after returns first trading day on or after."""
    result = closest_nyse_trading_day(date(2020, 1, 1), which="on_or_after")
    assert result is not None
    assert result.date() >= date(2020, 1, 1)
    # Jan 1 2020 is Wednesday (New Year), so first trading day is Jan 2
    assert result.date() == date(2020, 1, 2)


def test_closest_nyse_trading_day_on_or_before():
    """Dec 25 is closed; on_or_before returns last trading day on or before."""
    result = closest_nyse_trading_day(date(2019, 12, 25), which="on_or_before")
    assert result is not None
    assert result.date() <= date(2019, 12, 25)
    assert result.date() == date(2019, 12, 24)


def test_closest_nyse_trading_day_accepts_timestamp():
    """Target can be pd.Timestamp."""
    result = closest_nyse_trading_day(pd.Timestamp("2019-07-04"), which="closest")
    assert result is not None
    assert result.date() in (date(2019, 7, 3), date(2019, 7, 5))


def test_closest_nyse_trading_day_max_offset_returns_none_when_too_far():
    """When no trading day in range, returns None."""
    # Request a 1-day window around a holiday with max_offset_days=0: only that day is checked
    result = closest_nyse_trading_day(date(2019, 7, 4), which="closest", max_offset_days=0)
    assert result is None


def test_closest_nyse_trading_day_invalid_which_raises():
    """Invalid which raises ValueError."""
    with pytest.raises(ValueError, match="which must"):
        closest_nyse_trading_day(date(2019, 6, 15), which="invalid")
