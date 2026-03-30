from __future__ import annotations

import math

import pandas as pd
import pytest

from tiportfolio.algo import Context
from tiportfolio.algos.rebalance import Action
from tiportfolio.algos.select import Select
from tiportfolio.algos.signal import Signal
from tiportfolio.algos.weigh import Weigh
from tiportfolio.backtest import Backtest, execute_leaf_trades, mark_to_market, run
from tiportfolio.config import TiConfig
from tiportfolio.portfolio import Portfolio


# ---------------------------------------------------------------------------
# mark_to_market
# ---------------------------------------------------------------------------


class TestMarkToMarket:
    def test_with_positions(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio("test", [], ["QQQ"])
        p.cash = 5000.0
        p.positions = {"QQQ": 10.0}
        date = pd.Timestamp("2024-01-02", tz="UTC")
        mark_to_market(p, prices_dict, date)
        # QQQ close on 2024-01-02 = 101.00
        assert p.equity == pytest.approx(5000.0 + 10 * 101.0)

    def test_empty_portfolio(self) -> None:
        p = Portfolio("test", [], ["QQQ"])
        p.cash = 10_000.0
        p.positions = {}
        prices: dict[str, pd.DataFrame] = {}
        date = pd.Timestamp("2024-01-02", tz="UTC")
        mark_to_market(p, prices, date)
        assert p.equity == 10_000.0

    def test_multiple_positions(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio("test", [], ["QQQ", "BIL"])
        p.cash = 1000.0
        p.positions = {"QQQ": 5.0, "BIL": 10.0}
        date = pd.Timestamp("2024-01-02", tz="UTC")
        mark_to_market(p, prices_dict, date)
        # QQQ=101.00, BIL=91.55
        expected = 1000.0 + 5 * 101.0 + 10 * 91.55
        assert p.equity == pytest.approx(expected)


# ---------------------------------------------------------------------------
# execute_leaf_trades
# ---------------------------------------------------------------------------


class TestExecuteLeafTrades:
    def test_first_rebalance_from_cash(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio("test", [], ["QQQ", "BIL"])
        p.cash = 10_000.0
        p.equity = 10_000.0
        config = TiConfig()
        date = pd.Timestamp("2024-01-02", tz="UTC")

        ctx = Context(
            portfolio=p,
            prices=prices_dict,
            date=date,
            config=config,
        )
        ctx.selected = ["QQQ", "BIL"]
        ctx.weights = {"QQQ": 0.5, "BIL": 0.5}

        execute_leaf_trades(p, ctx)

        # target_value QQQ = 10000 * 0.5 = 5000, price=101.0, qty=5000/101 ≈ 49.505
        # target_value BIL = 10000 * 0.5 = 5000, price=91.55, qty=5000/91.55 ≈ 54.614
        expected_qqq = 5000.0 / 101.0
        expected_bil = 5000.0 / 91.55
        assert p.positions["QQQ"] == pytest.approx(expected_qqq)
        assert p.positions["BIL"] == pytest.approx(expected_bil)
        cost = expected_qqq * 101.0 + expected_bil * 91.55
        fees = (expected_qqq + expected_bil) * config.fee_per_share
        assert p.cash == pytest.approx(10_000.0 - cost - fees)

    def test_rebalance_sells_excess(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio("test", [], ["QQQ", "BIL"])
        p.positions = {"QQQ": 80.0, "BIL": 20.0}
        p.cash = 500.0
        config = TiConfig()
        date = pd.Timestamp("2024-01-02", tz="UTC")
        # QQQ=101, BIL=91.55
        p.equity = 500.0 + 80 * 101.0 + 20 * 91.55  # 10411.0

        ctx = Context(
            portfolio=p,
            prices=prices_dict,
            date=date,
            config=config,
        )
        ctx.selected = ["QQQ", "BIL"]
        ctx.weights = {"QQQ": 0.3, "BIL": 0.7}

        execute_leaf_trades(p, ctx)

        # equity = 10411.0
        # target QQQ: 10411 * 0.3 / 101 ≈ 30.924
        # target BIL: 10411 * 0.7 / 91.55 ≈ 79.596
        expected_qqq = 10411.0 * 0.3 / 101.0
        expected_bil = 10411.0 * 0.7 / 91.55
        assert p.positions["QQQ"] == pytest.approx(expected_qqq)
        assert p.positions["BIL"] == pytest.approx(expected_bil)


# ---------------------------------------------------------------------------
# Backtest constructor
# ---------------------------------------------------------------------------


class TestBacktestConstructor:
    def test_valid_construction(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio("test", [Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()], ["QQQ", "BIL", "GLD"])
        bt = Backtest(p, prices_dict)
        assert bt.config == TiConfig()

    def test_misaligned_data_rejected(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bad = prices_dict.copy()
        bad["BAD"] = prices_dict["QQQ"].iloc[:-5]
        p = Portfolio("test", [], ["QQQ"])
        with pytest.raises(ValueError):
            Backtest(p, bad)

    def test_custom_config(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        config = TiConfig(initial_capital=50_000)
        p = Portfolio("test", [], ["QQQ"])
        bt = Backtest(p, prices_dict, config=config)
        assert bt.config.initial_capital == 50_000

    def test_custom_fee_via_config(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio("test", [], ["QQQ"])
        config = TiConfig(fee_per_share=0.01)
        bt = Backtest(p, prices_dict, config=config)
        assert bt.config.fee_per_share == 0.01


# ---------------------------------------------------------------------------
# Integration: full backtest
# ---------------------------------------------------------------------------


class TestFullBacktest:
    def test_equity_curve_length(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio(
            "monthly",
            [Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()],
            ["QQQ", "BIL", "GLD"],
        )
        bt = Backtest(p, prices_dict)
        result = run(bt)
        single = result[0]
        expected_days = len(next(iter(prices_dict.values())))
        assert len(single.equity_curve) == expected_days

    def test_initial_equity(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio(
            "monthly",
            [Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()],
            ["QQQ", "BIL", "GLD"],
        )
        bt = Backtest(p, prices_dict)
        result = run(bt)
        single = result[0]
        # First bar equity = initial_capital (before any rebalance)
        assert single.equity_curve.iloc[0] == pytest.approx(10_000.0)

    def test_equity_changes_after_rebalance(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        p = Portfolio(
            "monthly",
            [Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()],
            ["QQQ", "BIL", "GLD"],
        )
        bt = Backtest(p, prices_dict)
        result = run(bt)
        single = result[0]
        # After Jan 31 rebalance, Feb 1 equity should differ from initial
        # (prices changed + positions held)
        last_equity = single.equity_curve.iloc[-1]
        assert last_equity != 10_000.0  # equity has changed

    def test_run_returns_backtest_result(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        from tiportfolio.result import BacktestResult

        p = Portfolio(
            "monthly",
            [Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()],
            ["QQQ", "BIL", "GLD"],
        )
        bt = Backtest(p, prices_dict)
        result = run(bt)
        assert isinstance(result, BacktestResult)
        assert result[0].name == "monthly"
