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
        algo = Signal.Schedule(day="end")
        ctx = _make_context("2024-02-29")
        assert algo(ctx) is True


class TestSignalScheduleStart:
    """Signal.Schedule with day='start' fires on first NYSE trading day of month."""

    def test_fires_on_first_trading_day(self) -> None:
        # Jan 2, 2024 is a Tuesday (Jan 1 is New Year's holiday)
        algo = Signal.Schedule(day="start")
        ctx = _make_context("2024-01-02")
        assert algo(ctx) is True

    def test_skips_non_first_day(self) -> None:
        algo = Signal.Schedule(day="start")
        ctx = _make_context("2024-01-03")
        assert algo(ctx) is False

    def test_first_day_is_weekend(self) -> None:
        # Jun 1, 2024 is a Saturday → first trading day is Mon Jun 3
        algo = Signal.Schedule(day="start")
        ctx = _make_context("2024-06-03")
        assert algo(ctx) is True
        ctx_sat = _make_context("2024-06-01")
        assert algo(ctx_sat) is False

    def test_with_month_filter(self) -> None:
        algo = Signal.Schedule(day="start", month=3)
        ctx_jan = _make_context("2024-01-02")
        assert algo(ctx_jan) is False
        # Mar 1, 2024 is a Friday (trading day)
        ctx_mar = _make_context("2024-03-01")
        assert algo(ctx_mar) is True


class TestSignalScheduleMid:
    """Signal.Schedule with day='mid' fires on first trading day on/after 15th."""

    def test_fires_on_15th_when_trading_day(self) -> None:
        # Jan 16, 2024 is a Tuesday (15th is MLK holiday) → forward to 16th
        algo = Signal.Schedule(day="mid")
        ctx = _make_context("2024-01-16")
        assert algo(ctx) is True

    def test_fires_when_15th_is_trading_day(self) -> None:
        # Mar 15, 2024 is a Friday (trading day)
        algo = Signal.Schedule(day="mid")
        ctx = _make_context("2024-03-15")
        assert algo(ctx) is True

    def test_forward_search_on_weekend(self) -> None:
        # Jun 15, 2024 is a Saturday → forward to Mon Jun 17
        algo = Signal.Schedule(day="mid")
        ctx = _make_context("2024-06-17")
        assert algo(ctx) is True
        ctx_sat = _make_context("2024-06-15")
        assert algo(ctx_sat) is False

    def test_strict_mode_rejects_non_trading_day(self) -> None:
        # Jun 15, 2024 is a Saturday
        algo = Signal.Schedule(day="mid", closest_trading_day=False)
        ctx = _make_context("2024-06-15")
        assert algo(ctx) is False
        # Monday should also not fire in strict mode
        ctx_mon = _make_context("2024-06-17")
        assert algo(ctx_mon) is False


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
        algo = Signal.Monthly()
        fire_dates = []
        for date in trading_dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        assert len(fire_dates) == 1
        assert fire_dates[0].month == 1
        assert fire_dates[0].day == 31

    def test_closest_trading_day_param(self) -> None:
        """Verify renamed param works."""
        algo = Signal.Monthly(day=15, closest_trading_day=True)
        ctx = _make_context("2024-01-16")  # 15th is MLK → forward to 16th
        assert algo(ctx) is True


class TestSignalScheduleIntDay:
    """Signal.Schedule with day=int resolves to NYSE trading days."""

    def test_fires_on_trading_day(self) -> None:
        algo = Signal.Schedule(day=15)
        ctx = _make_context("2024-01-16")  # 15th is MLK holiday, next trading day is 16th
        assert algo(ctx) is True

    def test_exact_day_is_trading_day(self) -> None:
        algo = Signal.Schedule(day=17)
        ctx = _make_context("2024-01-17")
        assert algo(ctx) is True

    def test_snaps_forward_on_weekend(self) -> None:
        algo = Signal.Schedule(day=13, closest_trading_day=True)
        ctx = _make_context("2024-01-16")  # 13th is Sat, 15th is MLK → 16th
        assert algo(ctx) is True

    def test_strict_mode_rejects_non_trading_day(self) -> None:
        algo = Signal.Schedule(day=13, closest_trading_day=False)
        ctx = _make_context("2024-01-13")
        assert algo(ctx) is False
        ctx2 = _make_context("2024-01-16")
        assert algo(ctx2) is False

    def test_day_31_in_february(self) -> None:
        algo = Signal.Schedule(day=31)
        ctx = _make_context("2024-02-29")
        assert algo(ctx) is False

    def test_month_filter_with_int_day(self) -> None:
        algo = Signal.Schedule(day=15, month=3)
        ctx_jan = _make_context("2024-01-16")
        assert algo(ctx_jan) is False
        ctx_mar = _make_context("2024-03-15")
        assert algo(ctx_mar) is True


class TestSignalQuarterly:
    """Signal.Quarterly fires on calendar quarters by default."""

    def test_default_fires_four_times_per_year(self) -> None:
        algo = Signal.Quarterly()
        fire_months: list[int] = []
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_months.append(date.month)
        assert len(fire_months) == 4
        assert set(fire_months) == {1, 4, 7, 10}

    def test_custom_months(self) -> None:
        algo = Signal.Quarterly(months=[3, 6, 9, 12])
        fire_months: list[int] = []
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_months.append(date.month)
        assert len(fire_months) == 4
        assert set(fire_months) == {3, 6, 9, 12}

    def test_skips_non_target_months(self) -> None:
        algo = Signal.Quarterly()
        ctx = _make_context("2024-02-29")  # Feb month-end — not in default quarterly months
        assert algo(ctx) is False

    def test_day_start(self) -> None:
        algo = Signal.Quarterly(day="start")
        fire_months: list[int] = []
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_months.append(date.month)
        assert len(fire_months) == 4
        assert set(fire_months) == {1, 4, 7, 10}

    def test_day_mid(self) -> None:
        algo = Signal.Quarterly(day="mid")
        fire_count = 0
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
                # Should fire on or after the 15th
                assert date.day >= 15
        assert fire_count == 4

    def test_day_int(self) -> None:
        algo = Signal.Quarterly(day=10)
        fire_count = 0
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
                assert date.day >= 10
        assert fire_count == 4


class TestSignalWeekly:
    """Signal.Weekly fires once per ISO week."""

    def test_default_end_of_week(self) -> None:
        algo = Signal.Weekly()
        fire_count = 0
        # Scan January 2024 (has 4 full weeks + partial)
        dates = pd.bdate_range("2024-01-01", "2024-01-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
        # Jan 2024 has ~4-5 weeks
        assert 4 <= fire_count <= 5

    def test_start_of_week(self) -> None:
        algo = Signal.Weekly(day="start")
        fire_dates: list[pd.Timestamp] = []
        # Use weeks without holidays: Feb 5-16, 2024 (2 full Mon-Fri weeks)
        dates = pd.bdate_range("2024-02-05", "2024-02-16", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        assert len(fire_dates) == 2
        for d in fire_dates:
            assert d.dayofweek == 0  # Monday

    def test_mid_week_on_or_after_wednesday(self) -> None:
        algo = Signal.Weekly(day="mid")
        fire_dates: list[pd.Timestamp] = []
        dates = pd.bdate_range("2024-01-08", "2024-01-19", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        assert len(fire_dates) == 2
        for d in fire_dates:
            assert d.dayofweek == 2  # Wednesday

    def test_short_week_with_holiday(self) -> None:
        # Jan 15, 2024 is MLK Day (Monday holiday)
        algo = Signal.Weekly(day="start")
        # Week of Jan 15-19: Monday is holiday, first trading day is Tuesday
        ctx_tue = _make_context("2024-01-16")
        assert algo(ctx_tue) is True


class TestSignalYearly:
    """Signal.Yearly fires once per year with year-level day resolution."""

    def test_default_end_of_year(self) -> None:
        algo = Signal.Yearly()
        fire_count = 0
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
        assert fire_count == 1

    def test_start_of_year(self) -> None:
        algo = Signal.Yearly(day="start")
        fire_dates: list[pd.Timestamp] = []
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        assert len(fire_dates) == 1
        assert fire_dates[0].month == 1

    def test_mid_year(self) -> None:
        algo = Signal.Yearly(day="mid")
        fire_dates: list[pd.Timestamp] = []
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        assert len(fire_dates) == 1
        assert fire_dates[0].month == 7

    def test_custom_month_override(self) -> None:
        algo = Signal.Yearly(day="end", month=6)
        fire_dates: list[pd.Timestamp] = []
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        assert len(fire_dates) == 1
        assert fire_dates[0].month == 6


class TestSignalEveryNPeriods:
    """Signal.EveryNPeriods fires every N-th period."""

    def test_every_2_days(self) -> None:
        algo = Signal.EveryNPeriods(n=2, period="day")
        fire_count = 0
        dates = pd.bdate_range("2024-01-02", "2024-01-19", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
        # 14 trading days → fires every 2nd → 7 fires
        assert fire_count == 7

    def test_biweekly(self) -> None:
        algo = Signal.EveryNPeriods(n=2, period="week")
        fire_count = 0
        dates = pd.bdate_range("2024-01-01", "2024-03-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
        # ~13 weeks in Q1 → fires ~6-7 times
        assert 5 <= fire_count <= 7

    def test_every_3_months(self) -> None:
        algo = Signal.EveryNPeriods(n=3, period="month")
        fire_count = 0
        dates = pd.bdate_range("2024-01-01", "2024-12-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_count += 1
        assert fire_count == 4

    def test_day_param_controls_target(self) -> None:
        algo = Signal.EveryNPeriods(n=1, period="month", day="start")
        fire_dates: list[pd.Timestamp] = []
        dates = pd.bdate_range("2024-01-01", "2024-03-31", freq="B")
        for date in dates:
            ctx = _make_context(str(date.date()))
            if algo(ctx):
                fire_dates.append(date)
        # Should fire on the first trading day of each month
        assert len(fire_dates) == 3
        for d in fire_dates:
            assert d.day <= 3  # first trading day is always within first 3 calendar days


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


class TestSignalVIX:
    """Signal.VIX regime switching with hysteresis."""

    def _make_vix_context(
        self, date: str, vix_close: float, children: list,
    ) -> Context:
        portfolio = MagicMock()
        portfolio.name = "regime"
        portfolio.children = children
        vix_idx = pd.DatetimeIndex([pd.Timestamp(date, tz="UTC")])
        vix_df = pd.DataFrame({"close": [vix_close]}, index=vix_idx)
        return Context(
            portfolio=portfolio,
            prices={},
            date=pd.Timestamp(date, tz="UTC"),
            config=TiConfig(),
        ), {"^VIX": vix_df}

    def test_below_low_selects_children_0(self) -> None:
        low_vol = MagicMock()
        low_vol.name = "low_vol"
        high_vol = MagicMock()
        high_vol.name = "high_vol"
        ctx, vix_data = self._make_vix_context("2024-01-02", 18.0, [low_vol, high_vol])
        algo = Signal.VIX(high=30, low=20, data=vix_data)
        result = algo(ctx)
        assert result is True
        assert ctx.selected == [low_vol]
        assert ctx.weights == {"low_vol": 1.0}

    def test_above_high_selects_children_1(self) -> None:
        low_vol = MagicMock()
        low_vol.name = "low_vol"
        high_vol = MagicMock()
        high_vol.name = "high_vol"
        ctx, vix_data = self._make_vix_context("2024-01-02", 35.0, [low_vol, high_vol])
        algo = Signal.VIX(high=30, low=20, data=vix_data)
        result = algo(ctx)
        assert result is True
        assert ctx.selected == [high_vol]

    def test_hysteresis_persists_previous(self) -> None:
        low_vol = MagicMock()
        low_vol.name = "low_vol"
        high_vol = MagicMock()
        high_vol.name = "high_vol"
        # First call: VIX=18 → selects low_vol
        ctx1, vix_data = self._make_vix_context("2024-01-02", 18.0, [low_vol, high_vol])
        algo = Signal.VIX(high=30, low=20, data=vix_data)
        algo(ctx1)
        assert ctx1.selected == [low_vol]
        # Second call: VIX=25 (between) → persists low_vol
        vix_data["^VIX"] = pd.DataFrame(
            {"close": [25.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-03", tz="UTC")]),
        )
        ctx2, _ = self._make_vix_context("2024-01-03", 25.0, [low_vol, high_vol])
        algo(ctx2)
        assert ctx2.selected == [low_vol]

    def test_lazy_init_defaults_to_children_0(self) -> None:
        low_vol = MagicMock()
        low_vol.name = "low_vol"
        high_vol = MagicMock()
        high_vol.name = "high_vol"
        # VIX=25 on first call (between thresholds) → defaults to children[0]
        ctx, vix_data = self._make_vix_context("2024-01-02", 25.0, [low_vol, high_vol])
        algo = Signal.VIX(high=30, low=20, data=vix_data)
        algo(ctx)
        assert ctx.selected == [low_vol]
