"""Tests for Signal.Indicator — technical indicator crossover signal."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest

from tiportfolio.algo import Context, Or
from tiportfolio.algos.signal import Signal
from tiportfolio.config import TiConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prices(close_values: list[float], start: str = "2020-01-02") -> dict[str, pd.DataFrame]:
    """Build a prices dict with a single ticker 'TEST' from close values."""
    dates = pd.bdate_range(start, periods=len(close_values), tz="UTC")
    df = pd.DataFrame({"close": close_values}, index=dates)
    return {"TEST": df}


def _make_context(
    prices: dict[str, pd.DataFrame],
    date: pd.Timestamp,
) -> Context:
    return Context(
        portfolio=None,  # type: ignore[arg-type]
        prices=prices,
        date=date,
        config=TiConfig(),
    )


def _sma_cross_condition(short: int = 5, long: int = 20) -> callable:
    """Return a condition: SMA(short) > SMA(long)."""
    def condition(close: pd.Series) -> bool:  # type: ignore[type-arg]
        if len(close) < long:
            return False
        sma_short = close.rolling(short).mean().iloc[-1]
        sma_long = close.rolling(long).mean().iloc[-1]
        return bool(sma_short > sma_long)
    return condition


def _build_crossover_prices(n: int = 100, cross_bar: int = 60) -> list[float]:
    """Build prices that start declining (short SMA < long SMA), then rise
    sharply so short SMA crosses above long SMA around bar `cross_bar`.

    Uses short=5 / long=20 SMA pair for fast crossover in synthetic data.
    """
    prices = []
    for i in range(n):
        if i < cross_bar:
            # Gentle decline: 100 → ~85
            prices.append(100.0 - i * 0.25)
        else:
            # Sharp rise from the bottom
            base = prices[cross_bar - 1]
            prices.append(base + (i - cross_bar + 1) * 1.5)
    return prices


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSignalIndicator:
    def test_cross_up_fires_on_transition(self) -> None:
        """cross='up' fires exactly once when condition transitions False→True."""
        close_values = _build_crossover_prices(n=100, cross_bar=60)
        prices = _make_prices(close_values)
        dates = prices["TEST"].index
        condition = _sma_cross_condition(short=5, long=20)

        indicator = Signal.Indicator(
            ticker="TEST",
            condition=condition,
            lookback=pd.DateOffset(days=365),
            cross="up",
        )

        fire_dates = []
        for date in dates:
            ctx = _make_context(prices, date)
            if indicator(ctx):
                fire_dates.append(date)

        # Should fire exactly once (the crossover bar)
        assert len(fire_dates) == 1
        # The crossover should happen after the sharp rise begins
        assert fire_dates[0] > dates[60]

    def test_cross_down_fires_on_transition(self) -> None:
        """cross='down' fires when condition transitions True→False."""
        # Rise sharply first (SMA5 > SMA20 = True), then decline (→ False)
        rise = [50.0 + i * 1.5 for i in range(50)]
        decline = [rise[-1] - (i + 1) * 1.0 for i in range(50)]
        close_values = rise + decline
        prices = _make_prices(close_values)
        dates = prices["TEST"].index
        condition = _sma_cross_condition(short=5, long=20)

        indicator = Signal.Indicator(
            ticker="TEST",
            condition=condition,
            lookback=pd.DateOffset(days=365),
            cross="down",
        )

        fire_dates = []
        for date in dates:
            ctx = _make_context(prices, date)
            if indicator(ctx):
                fire_dates.append(date)

        # Should fire at least once (True→False when decline causes SMA5 < SMA20)
        assert len(fire_dates) >= 1

    def test_cross_both_fires_on_either_direction(self) -> None:
        """cross='both' fires on any state change."""
        # Create V-shape: decline then rise — gives cross-down then cross-up
        decline = [100.0 - i * 1.0 for i in range(50)]
        rise = [decline[-1] + (i + 1) * 1.5 for i in range(50)]
        close_values = decline + rise
        prices = _make_prices(close_values)
        dates = prices["TEST"].index
        condition = _sma_cross_condition(short=5, long=20)

        indicator = Signal.Indicator(
            ticker="TEST",
            condition=condition,
            lookback=pd.DateOffset(days=365),
            cross="both",
        )

        fire_count = 0
        for date in dates:
            ctx = _make_context(prices, date)
            if indicator(ctx):
                fire_count += 1

        # Should fire at least once (the up-cross after the V bottom)
        assert fire_count >= 1

    def test_first_bar_never_fires(self) -> None:
        """First call initialises state but never fires."""
        prices = _make_prices([100.0, 101.0, 102.0])
        dates = prices["TEST"].index

        # Condition always True
        indicator = Signal.Indicator(
            ticker="TEST",
            condition=lambda s: True,
            lookback=pd.DateOffset(days=365),
            cross="up",
        )

        ctx = _make_context(prices, dates[0])
        assert indicator(ctx) is False  # first bar — never fires

    def test_invalid_cross_raises_valueerror(self) -> None:
        with pytest.raises(ValueError, match="cross must be one of"):
            Signal.Indicator(
                ticker="TEST",
                condition=lambda s: True,
                lookback=pd.DateOffset(days=30),
                cross="invalid",
            )

    def test_missing_ticker_returns_false(self) -> None:
        prices = _make_prices([100.0, 101.0])
        dates = prices["TEST"].index

        indicator = Signal.Indicator(
            ticker="MISSING",
            condition=lambda s: True,
            lookback=pd.DateOffset(days=30),
        )

        ctx = _make_context(prices, dates[0])
        assert indicator(ctx) is False

    def test_steady_state_does_not_fire(self) -> None:
        """Same state on consecutive bars → no fire."""
        # Steadily rising prices: condition always True after warmup
        close_values = [100.0 + i * 0.5 for i in range(100)]
        prices = _make_prices(close_values)
        dates = prices["TEST"].index
        condition = _sma_cross_condition(short=5, long=20)

        indicator = Signal.Indicator(
            ticker="TEST",
            condition=condition,
            lookback=pd.DateOffset(days=365),
            cross="up",
        )

        fire_count = 0
        for date in dates:
            ctx = _make_context(prices, date)
            if indicator(ctx):
                fire_count += 1

        # Steadily rising: SMA5 > SMA20 from early on, maybe one transition max
        # After first True state is established, no more fires
        assert fire_count <= 1

    def test_composable_with_or(self) -> None:
        """Signal.Indicator works inside Or() combinator."""
        prices = _make_prices([100.0, 101.0, 102.0])
        dates = prices["TEST"].index

        indicator = Signal.Indicator(
            ticker="TEST",
            condition=lambda s: True,
            lookback=pd.DateOffset(days=365),
            cross="up",
        )
        monthly = Signal.Monthly()

        combined = Or(monthly, indicator)
        # Should not raise — just verify it's callable
        ctx = _make_context(prices, dates[0])
        result = combined(ctx)
        assert isinstance(result, bool)
