"""Tests for AllocationStrategy, VixRegimeAllocation, VixChangeFilter, VolatilityBasedEngine."""

import pandas as pd
import pytest

from tiportfolio import (
    FixRatio,
    Schedule,
    VixChangeFilter,
    VixRegimeAllocation,
    VolatilityBasedEngine,
)
from tiportfolio.allocation import validate_vix_regime_bounds


def test_fix_ratio_get_symbols():
    """FixRatio.get_symbols() returns keys of weights."""
    fr = FixRatio(weights={"A": 0.5, "B": 0.5})
    assert fr.get_symbols() == ["A", "B"] or set(fr.get_symbols()) == {"A", "B"}


def test_fix_ratio_get_target_weights_ignores_context():
    """FixRatio.get_target_weights returns fixed weights regardless of date/context."""
    fr = FixRatio(weights={"A": 0.6, "B": 0.4})
    row = pd.Series({"A": 100.0, "B": 50.0})
    w = fr.get_target_weights(
        pd.Timestamp("2020-01-15"), 10000.0, {"A": 5000.0, "B": 5000.0}, row, vix_at_date=30.0
    )
    assert w == {"A": 0.6, "B": 0.4}


def test_vix_regime_allocation_high_low_by_context():
    """VixRegimeAllocation returns high_vol weights when use_high_vol_allocation=True, low_vol when False."""
    high = FixRatio(weights={"A": 0.4, "B": 0.6})
    low = FixRatio(weights={"A": 0.7, "B": 0.3})
    strat = VixRegimeAllocation(
        high_vol_allocation=high,
        low_vol_allocation=low,
    )
    row = pd.Series({"A": 1.0, "B": 1.0})
    eq, pos = 1000.0, {"A": 500.0, "B": 500.0}

    w_high = strat.get_target_weights(
        pd.Timestamp("2020-01-01"), eq, pos, row, use_high_vol_allocation=True
    )
    assert w_high["A"] == 0.4 and w_high["B"] == 0.6

    w_low = strat.get_target_weights(
        pd.Timestamp("2020-01-01"), eq, pos, row, use_high_vol_allocation=False
    )
    assert w_low["A"] == 0.7 and w_low["B"] == 0.3

    w_default = strat.get_target_weights(
        pd.Timestamp("2020-01-01"), eq, pos, row
    )
    assert w_default["A"] == 0.7 and w_default["B"] == 0.3


def test_vix_regime_allocation_same_symbols():
    """VixRegimeAllocation requires same symbols in high and low allocations."""
    high = FixRatio(weights={"A": 0.5, "B": 0.5})
    low = FixRatio(weights={"A": 0.5, "B": 0.5})
    low_extra = FixRatio(weights={"A": 0.33, "B": 0.33, "C": 0.34})
    with pytest.raises(ValueError, match="same symbols"):
        VixRegimeAllocation(
            high_vol_allocation=high,
            low_vol_allocation=low_extra,
        )


def test_validate_vix_regime_bounds():
    """_validate_vix_regime_bounds raises when lower > upper."""
    validate_vix_regime_bounds(20.0, -1.0, 10.0)
    with pytest.raises(ValueError, match="lower_bound <= upper_bound"):
        validate_vix_regime_bounds(20.0, 10.0, -1.0)


def test_vix_change_filter_delta_abs():
    """VixChangeFilter returns True when abs(vix_now - vix_month_ago) >= delta_abs."""
    vix = pd.Series(
        [20.0, 20.0, 35.0],
        index=pd.DatetimeIndex(["2020-01-15", "2020-02-15", "2020-03-15"]),
    )
    f = VixChangeFilter(delta_abs=10.0, delta_pct=0.20)
    # At 2020-03-15: vix_now=35, vix_month_ago (2020-02-15)=20, diff=15 >= 10
    assert f(pd.Timestamp("2020-03-15"), vix, None) is True


def test_vix_change_filter_delta_pct():
    """VixChangeFilter returns True when pct change vs last rebalance >= delta_pct."""
    vix = pd.Series(
        [20.0, 25.0],
        index=pd.DatetimeIndex(["2020-01-15", "2020-02-15"]),
    )
    f = VixChangeFilter(delta_abs=100.0, delta_pct=0.20)
    # vix_now=25, vix_last=20, (25-20)/20=0.25 >= 0.20
    assert f(pd.Timestamp("2020-02-15"), vix, pd.Timestamp("2020-01-15")) is True


def test_vix_change_filter_no_div_zero():
    """VixChangeFilter does not raise when vix_last is 0 (skips pct check)."""
    vix = pd.Series(
        [0.0, 10.0],
        index=pd.DatetimeIndex(["2020-01-15", "2020-02-15"]),
    )
    f = VixChangeFilter(delta_abs=100.0, delta_pct=0.20)
    # vix_last=0 would cause div by zero in pct check; implementation skips it
    result = f(pd.Timestamp("2020-02-15"), vix, pd.Timestamp("2020-01-15"))
    # Should not raise; result can be True (delta_abs) or False
    assert result in (True, False)


def test_volatility_based_engine_vix_regime_synthetic():
    """VolatilityBasedEngine with vix_regime uses VixRegimeAllocation and rebalances on crosses."""
    # 10 trading days; VIX 25,25,25,25,25,32,32,32,32,32 -> cross above 30 on day 5
    ix = pd.date_range("2019-01-02", periods=10, freq="B")
    n = len(ix)
    prices = {
        "SPY": pd.DataFrame({"close": [280.0 + i * 0.1 for i in range(n)]}, index=ix),
        "QQQ": pd.DataFrame({"close": [180.0 + i * 0.1 for i in range(n)]}, index=ix),
        "GLD": pd.DataFrame({"close": [120.0 + i * 0.1 for i in range(n)]}, index=ix),
        "VIX": pd.DataFrame(
            {"close": [25.0] * 5 + [32.0] * 5},
            index=ix,
        ),
    }
    allocation = VixRegimeAllocation(
        high_vol_allocation=FixRatio(weights={"SPY": 0.33, "QQQ": 0.33, "GLD": 0.34}),
        low_vol_allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}),
    )
    engine = VolatilityBasedEngine(
        allocation=allocation,
        rebalance=Schedule("vix_regime"),
        fee_per_share=0,
    )
    result = engine.run(
        symbols=["SPY", "QQQ", "GLD"],
        start=ix[0],
        end=ix[-1],
        prices_df=prices,
        volatility_symbol="VIX",
        target_vix=20.0,
        lower_bound=-1.0,
        upper_bound=10.0,
    )
    assert result.equity_curve is not None
    assert len(result.equity_curve) == n
    # One rebalance (cross above 30 on day 5)
    assert len(result.rebalance_decisions) >= 1
    first_dec = result.rebalance_decisions[0]
    assert first_dec.target_weights["SPY"] == pytest.approx(0.33, abs=0.01)
