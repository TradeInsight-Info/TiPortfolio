"""Tests for run_backtest() prices_history context injection."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from tiportfolio.backtest import run_backtest


class _SpyStrategy:
    """Strategy that records every context dict passed to get_target_weights."""

    def __init__(self, symbols: list[str]) -> None:
        self._symbols = symbols
        self.captured_contexts: list[dict[str, Any]] = []

    def get_symbols(self) -> list[str]:
        return list(self._symbols)

    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        self.captured_contexts.append(dict(context))
        n = len(self._symbols)
        return {s: 1.0 / n for s in self._symbols}


def _make_prices_df(symbols: list[str], n: int = 15) -> pd.DataFrame:
    dates = pd.date_range("2020-01-02", periods=n, freq="B", tz="UTC")
    data = {s: [100.0 + i + j for i in range(n)] for j, s in enumerate(symbols)}
    return pd.DataFrame(data, index=dates)


def test_run_backtest_passes_prices_history_on_rebalance():
    """run_backtest() passes prices_history=prices_df.loc[:date] on every rebalance call."""
    symbols = ["A", "B"]
    prices_df = _make_prices_df(symbols, n=30)
    spy = _SpyStrategy(symbols)

    run_backtest(
        prices_df,
        spy,
        schedule_spec="month_end",
        fee_per_share=0.0,
        start=None,
        end=None,
    )

    # At least one rebalance should have occurred
    assert len(spy.captured_contexts) >= 1
    for ctx in spy.captured_contexts:
        assert "prices_history" in ctx, "prices_history missing from context"
        ph = ctx["prices_history"]
        assert isinstance(ph, pd.DataFrame)
        assert set(symbols).issubset(ph.columns)


def test_run_backtest_prices_history_is_cumulative_slice():
    """prices_history grows over time — each call receives all rows up to and including the rebalance date."""
    symbols = ["X"]
    prices_df = _make_prices_df(symbols, n=60)
    spy = _SpyStrategy(symbols)

    run_backtest(
        prices_df,
        spy,
        schedule_spec="month_end",
        fee_per_share=0.0,
        start=None,
        end=None,
    )

    sizes = [len(ctx["prices_history"]) for ctx in spy.captured_contexts if "prices_history" in ctx]
    # Each successive rebalance should have >= rows than the previous
    assert sizes == sorted(sizes), "prices_history should grow monotonically"
