"""Tests for parent/child portfolio tree engine: mark-to-market, equity allocation, child liquidation."""
from __future__ import annotations

import pandas as pd
import pytest

from tiportfolio.algo import Context
from tiportfolio.backtest import (
    Backtest,
    _init_portfolio,
    _liquidate_child,
    allocate_equity_to_children,
    mark_to_market,
    run,
)
from tiportfolio.config import TiConfig
from tiportfolio.portfolio import Portfolio


def _make_prices(date: str, close: float = 100.0) -> dict[str, pd.DataFrame]:
    idx = pd.DatetimeIndex([pd.Timestamp(date, tz="UTC")])
    df = pd.DataFrame({"close": [close]}, index=idx)
    return {"QQQ": df, "BIL": df, "GLD": df}


# ---------------------------------------------------------------------------
# Mark-to-market
# ---------------------------------------------------------------------------


class TestRecursiveMarkToMarket:
    def test_leaf_unchanged(self) -> None:
        leaf = Portfolio("leaf", [], ["QQQ"])
        leaf.cash = 5000.0
        leaf.positions = {"QQQ": 10.0}
        prices = _make_prices("2024-01-02", close=200.0)
        mark_to_market(leaf, prices, pd.Timestamp("2024-01-02", tz="UTC"))
        assert leaf.equity == pytest.approx(7000.0)  # 5000 + 10*200

    def test_parent_equity_is_sum_of_children(self) -> None:
        child_a = Portfolio("a", [], ["QQQ"])
        child_b = Portfolio("b", [], ["QQQ"])
        child_a.cash = 6000.0
        child_a.positions = {}
        child_b.cash = 4000.0
        child_b.positions = {}
        parent = Portfolio("parent", [], [child_a, child_b])
        parent.cash = 0.0
        parent.positions = {}
        prices = _make_prices("2024-01-02")
        mark_to_market(parent, prices, pd.Timestamp("2024-01-02", tz="UTC"))
        assert parent.equity == pytest.approx(10000.0)

    def test_parent_with_zero_equity_child(self) -> None:
        child_a = Portfolio("a", [], ["QQQ"])
        child_b = Portfolio("b", [], ["QQQ"])
        child_a.cash = 10000.0
        child_a.positions = {}
        child_b.cash = 0.0
        child_b.positions = {}
        parent = Portfolio("parent", [], [child_a, child_b])
        parent.cash = 0.0
        parent.positions = {}
        prices = _make_prices("2024-01-02")
        mark_to_market(parent, prices, pd.Timestamp("2024-01-02", tz="UTC"))
        assert parent.equity == pytest.approx(10000.0)


# ---------------------------------------------------------------------------
# Parent initialisation
# ---------------------------------------------------------------------------


class TestParentInit:
    def test_root_parent_init(self) -> None:
        child_a = Portfolio("a", [], ["QQQ"])
        child_b = Portfolio("b", [], ["QQQ"])
        parent = Portfolio("parent", [], [child_a, child_b])
        _init_portfolio(parent, 10000.0)
        assert parent.cash == 10000.0  # parent holds capital until first allocation
        assert parent.equity == 10000.0
        assert parent.positions == {}
        assert child_a.cash == 0.0
        assert child_a.equity == 0.0
        assert child_b.cash == 0.0
        assert child_b.equity == 0.0

    def test_leaf_init(self) -> None:
        leaf = Portfolio("leaf", [], ["QQQ"])
        _init_portfolio(leaf, 10000.0)
        assert leaf.cash == 10000.0
        assert leaf.equity == 10000.0


# ---------------------------------------------------------------------------
# Child liquidation
# ---------------------------------------------------------------------------


class TestLiquidateChild:
    def test_sell_all_positions(self) -> None:
        child = Portfolio("child", [], ["QQQ"])
        child.cash = 0.0
        child.positions = {"QQQ": 100.0}
        prices = _make_prices("2024-01-02", close=200.0)
        config = TiConfig(fee_per_share=0.0035)
        _liquidate_child(child, prices, pd.Timestamp("2024-01-02", tz="UTC"), config)
        assert child.positions == {}
        expected_cash = 100 * 200 - 100 * 0.0035
        assert child.cash == pytest.approx(expected_cash)


# ---------------------------------------------------------------------------
# Equity allocation
# ---------------------------------------------------------------------------


class TestAllocateEquityToChildren:
    def test_equal_split(self) -> None:
        child_a = Portfolio("a", [], ["QQQ"])
        child_b = Portfolio("b", [], ["QQQ"])
        child_a.equity = 5000.0
        child_a.cash = 0.0
        child_a.positions = {}
        child_b.equity = 5000.0
        child_b.cash = 0.0
        child_b.positions = {}
        parent = Portfolio("parent", [], [child_a, child_b])
        parent.cash = 0.0

        ctx = Context(
            portfolio=parent,
            prices={},
            date=pd.Timestamp("2024-01-02", tz="UTC"),
            config=TiConfig(),
            selected=[child_a, child_b],
            weights={"a": 0.5, "b": 0.5},
        )
        allocate_equity_to_children(parent, ctx)
        assert child_a.equity == pytest.approx(5000.0)
        assert child_b.equity == pytest.approx(5000.0)

    def test_deselected_child_zeroed(self) -> None:
        child_a = Portfolio("a", [], ["QQQ"])
        child_b = Portfolio("b", [], ["QQQ"])
        child_a.equity = 5000.0
        child_a.cash = 0.0
        child_a.positions = {}
        child_b.equity = 5000.0
        child_b.cash = 0.0
        child_b.positions = {}
        parent = Portfolio("parent", [], [child_a, child_b])
        parent.cash = 0.0

        ctx = Context(
            portfolio=parent,
            prices={},
            date=pd.Timestamp("2024-01-02", tz="UTC"),
            config=TiConfig(),
            selected=[child_a],
            weights={"a": 1.0},
        )
        allocate_equity_to_children(parent, ctx)
        assert child_a.equity == pytest.approx(10000.0)
        assert child_b.equity == 0.0
        assert child_b.cash == 0.0

    def test_parent_cash_invariant(self) -> None:
        child_a = Portfolio("a", [], ["QQQ"])
        child_a.equity = 10000.0
        child_a.cash = 0.0
        child_a.positions = {}
        parent = Portfolio("parent", [], [child_a])
        parent.cash = 0.0

        ctx = Context(
            portfolio=parent,
            prices={},
            date=pd.Timestamp("2024-01-02", tz="UTC"),
            config=TiConfig(),
            selected=[child_a],
            weights={"a": 1.0},
        )
        allocate_equity_to_children(parent, ctx)
        assert parent.cash == 0.0


# ---------------------------------------------------------------------------
# Parent portfolio E2E
# ---------------------------------------------------------------------------


class TestParentE2E:
    def test_parent_runs_without_error(self) -> None:
        """Parent portfolio with two leaf children should run a backtest."""
        from tiportfolio.algos.rebalance import Action
        from tiportfolio.algos.select import Select
        from tiportfolio.algos.signal import Signal
        from tiportfolio.algos.weigh import Weigh

        tickers = ["QQQ", "BIL"]
        dates = pd.bdate_range("2024-01-02", "2024-02-01", freq="B")
        idx = dates.tz_localize("UTC")
        prices = {}
        for t in tickers:
            prices[t] = pd.DataFrame(
                {"close": [100.0 + i for i in range(len(idx))]},
                index=idx,
            )

        child_a = Portfolio(
            "child_a",
            [Select.All(), Weigh.Equally(), Action.Rebalance()],
            tickers,
        )
        child_b = Portfolio(
            "child_b",
            [Select.All(), Weigh.Equally(), Action.Rebalance()],
            tickers,
        )
        parent = Portfolio(
            "parent",
            [Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()],
            [child_a, child_b],
        )

        result = run(Backtest(parent, prices))
        summary = result.summary()
        assert "total_return" in summary.index
