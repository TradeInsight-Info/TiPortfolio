"""Tests for daily carry costs: short borrow and leverage loan."""
from __future__ import annotations

import pandas as pd
import pytest

from tiportfolio.backtest import deduct_daily_carry_costs
from tiportfolio.config import TiConfig
from tiportfolio.portfolio import Portfolio


def _make_prices(date: str, close: float = 200.0) -> dict[str, pd.DataFrame]:
    idx = pd.DatetimeIndex([pd.Timestamp(date, tz="UTC")])
    return {"QQQ": pd.DataFrame({"close": [close]}, index=idx)}


DATE = pd.Timestamp("2024-01-02", tz="UTC")


class TestShortBorrowCost:
    def test_short_position_deducts_borrow(self) -> None:
        p = Portfolio("p", [], ["QQQ"])
        p.cash = 10000.0
        p.equity = 10000.0
        p.positions = {"QQQ": -100.0}  # short 100 shares
        config = TiConfig(stock_borrow_rate=0.07, bars_per_year=252)
        prices = _make_prices("2024-01-02", close=200.0)
        cash_before = p.cash
        deduct_daily_carry_costs(p, prices, DATE, config)
        expected_cost = abs(-100 * 200) * 0.07 / 252
        assert p.cash == pytest.approx(cash_before - expected_cost)

    def test_no_cost_for_long_position(self) -> None:
        p = Portfolio("p", [], ["QQQ"])
        p.cash = 5000.0
        p.equity = 10000.0
        p.positions = {"QQQ": 50.0}  # long only, not leveraged
        config = TiConfig()
        prices = _make_prices("2024-01-02", close=100.0)
        cash_before = p.cash
        deduct_daily_carry_costs(p, prices, DATE, config)
        # equity=10000, long_value=50*100=5000 < equity → no leverage cost
        assert p.cash == pytest.approx(cash_before)


class TestLeverageLoanCost:
    def test_leveraged_long_deducts_loan(self) -> None:
        p = Portfolio("p", [], ["QQQ"])
        p.cash = -5000.0  # borrowed to buy more
        p.equity = 10000.0
        p.positions = {"QQQ": 75.0}  # 75 * 200 = 15000 > equity 10000
        config = TiConfig(loan_rate=0.0514, bars_per_year=252)
        prices = _make_prices("2024-01-02", close=200.0)
        cash_before = p.cash
        deduct_daily_carry_costs(p, prices, DATE, config)
        expected_cost = (15000 - 10000) * 0.0514 / 252
        assert p.cash == pytest.approx(cash_before - expected_cost)

    def test_no_cost_when_not_leveraged(self) -> None:
        p = Portfolio("p", [], ["QQQ"])
        p.cash = 5000.0
        p.equity = 10000.0
        p.positions = {"QQQ": 25.0}  # 25 * 200 = 5000 < equity
        config = TiConfig()
        prices = _make_prices("2024-01-02", close=200.0)
        cash_before = p.cash
        deduct_daily_carry_costs(p, prices, DATE, config)
        assert p.cash == pytest.approx(cash_before)


class TestRecursiveCarryCosts:
    def test_parent_recurses_into_children(self) -> None:
        child_with_short = Portfolio("short_child", [], ["QQQ"])
        child_with_short.cash = 5000.0
        child_with_short.equity = 5000.0
        child_with_short.positions = {"QQQ": -50.0}

        child_long_only = Portfolio("long_child", [], ["QQQ"])
        child_long_only.cash = 5000.0
        child_long_only.equity = 5000.0
        child_long_only.positions = {"QQQ": 10.0}

        parent = Portfolio("parent", [], [child_with_short, child_long_only])
        parent.cash = 0.0
        parent.equity = 10000.0
        parent.positions = {}

        config = TiConfig(stock_borrow_rate=0.07, bars_per_year=252)
        prices = _make_prices("2024-01-02", close=200.0)

        short_cash_before = child_with_short.cash
        long_cash_before = child_long_only.cash

        deduct_daily_carry_costs(parent, prices, DATE, config)

        # Short child should have cost deducted
        expected_cost = abs(-50 * 200) * 0.07 / 252
        assert child_with_short.cash == pytest.approx(short_cash_before - expected_cost)
        # Long child (not leveraged) should be unchanged
        assert child_long_only.cash == pytest.approx(long_cash_before)
