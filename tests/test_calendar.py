"""Tests for rebalance calendar."""

import pandas as pd
import pytest

from tiportfolio.calendar import VALID_SCHEDULES, Schedule, get_rebalance_dates


def test_schedule_accepts_valid_specs():
    """Schedule accepts all valid specs; rejects unknown."""
    for spec in VALID_SCHEDULES:
        s = Schedule(spec)
        assert s.spec == spec
    with pytest.raises(ValueError, match="schedule must"):
        Schedule("weekly")


def test_get_rebalance_dates_month_end_subset_of_index():
    """month_end rebalance dates are subset of trading_dates."""
    trading = pd.date_range("2019-01-02", "2020-06-30", freq="B")
    dates = get_rebalance_dates(trading, "month_end")
    assert dates.isin(trading).all()
    assert len(dates) >= 6  # at least 6 months


def test_get_rebalance_dates_quarter_end():
    """quarter_end produces one date per quarter."""
    trading = pd.date_range("2019-01-02", "2020-12-31", freq="B")
    dates = get_rebalance_dates(trading, "quarter_end")
    assert dates.isin(trading).all()
    assert 4 <= len(dates) <= 8  # roughly 2 years -> 8 quarters


def test_get_rebalance_dates_quarter_start():
    """quarter_start produces one date per quarter start."""
    trading = pd.date_range("2019-01-02", "2020-12-31", freq="B")
    dates = get_rebalance_dates(trading, "quarter_start")
    assert dates.isin(trading).all()
    assert 4 <= len(dates) <= 8


def test_get_rebalance_dates_month_mid():
    """month_mid produces about one date per month (15th or closest)."""
    trading = pd.date_range("2019-01-02", "2020-06-30", freq="B")
    dates = get_rebalance_dates(trading, "month_mid")
    assert dates.isin(trading).all()
    assert 12 <= len(dates) <= 20  # ~18 months


def test_get_rebalance_dates_quarter_mid():
    """quarter_mid produces about 4 dates per year (Feb15, May15, Aug15, Nov15)."""
    trading = pd.date_range("2019-01-02", "2020-12-31", freq="B")
    dates = get_rebalance_dates(trading, "quarter_mid")
    assert dates.isin(trading).all()
    assert 4 <= len(dates) <= 10


def test_get_rebalance_dates_year_start():
    """year_start produces one date per year."""
    trading = pd.date_range("2019-01-02", "2022-06-30", freq="B")
    dates = get_rebalance_dates(trading, "year_start")
    assert dates.isin(trading).all()
    assert 3 <= len(dates) <= 5


def test_get_rebalance_dates_year_mid():
    """year_mid produces one date per year (July 1 or closest)."""
    trading = pd.date_range("2019-01-02", "2022-06-30", freq="B")
    dates = get_rebalance_dates(trading, "year_mid")
    assert dates.isin(trading).all()
    assert 2 <= len(dates) <= 5


def test_get_rebalance_dates_vix_regime_crosses():
    """vix_regime returns dates when VIX crosses above (target+upper) or below (target+lower)."""
    # 5 trading days; VIX goes 25 -> 31 (cross above 30) -> 28 -> 18 (cross below 19) -> 22
    trading = pd.DatetimeIndex(
        [
            pd.Timestamp("2020-01-06"),
            pd.Timestamp("2020-01-07"),
            pd.Timestamp("2020-01-08"),
            pd.Timestamp("2020-01-09"),
            pd.Timestamp("2020-01-10"),
        ]
    )
    vix_series = pd.Series(
        [25.0, 31.0, 28.0, 18.0, 22.0],
        index=trading,
    )
    dates = get_rebalance_dates(
        trading,
        "vix_regime",
        vix_series=vix_series,
        target_vix=20.0,
        lower_bound=-1.0,
        upper_bound=10.0,
    )
    # Cross above 30 on 2020-01-07 (prev 25 < 30, curr 31 >= 30)
    # Cross below 19 on 2020-01-09 (prev 28 > 19, curr 18 <= 19)
    assert len(dates) == 2
    assert pd.Timestamp("2020-01-07") in dates
    assert pd.Timestamp("2020-01-09") in dates


def test_get_rebalance_dates_vix_regime_requires_params():
    """vix_regime raises when vix_series or band params missing."""
    trading = pd.date_range("2020-01-06", periods=5, freq="B")
    vix_series = pd.Series(25.0, index=trading)
    with pytest.raises(ValueError, match="requires vix_series"):
        get_rebalance_dates(trading, "vix_regime")
    with pytest.raises(ValueError, match="requires"):
        get_rebalance_dates(
            trading,
            "vix_regime",
            vix_series=vix_series,
            target_vix=20.0,
            # missing lower_bound, upper_bound
        )
