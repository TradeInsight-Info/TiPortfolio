from __future__ import annotations

from tiportfolio.algo import Algo, AlgoQueue, Context
from tiportfolio.portfolio import Portfolio


class _StubAlgo(Algo):
    def __call__(self, context: Context) -> bool:
        return True


class TestPortfolioConstruction:
    def test_name(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ", "BIL"])
        assert p.name == "test"

    def test_children_list_str(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ", "BIL"])
        assert p.children == ["QQQ", "BIL"]

    def test_children_none(self) -> None:
        p = Portfolio("test", [_StubAlgo()], None)
        assert p.children is None

    def test_algo_queue_wrapping(self) -> None:
        algos = [_StubAlgo(), _StubAlgo()]
        p = Portfolio("test", algos, ["QQQ"])
        assert isinstance(p.algo_queue, AlgoQueue)

    def test_children_list_portfolio(self) -> None:
        child = Portfolio("child", [_StubAlgo()], ["QQQ"])
        parent = Portfolio("parent", [_StubAlgo()], [child])
        assert parent.children == [child]
        assert isinstance(parent.children[0], Portfolio)


class TestPortfolioInitialState:
    def test_positions_empty(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ"])
        assert p.positions == {}

    def test_cash_zero(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ"])
        assert p.cash == 0.0

    def test_equity_zero(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ"])
        assert p.equity == 0.0


class TestPortfolioMutable:
    def test_cash_mutable(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ"])
        p.cash = 10_000.0
        assert p.cash == 10_000.0

    def test_positions_mutable(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ"])
        p.positions = {"QQQ": 50.0}
        assert p.positions == {"QQQ": 50.0}

    def test_equity_mutable(self) -> None:
        p = Portfolio("test", [_StubAlgo()], ["QQQ"])
        p.equity = 15_000.0
        assert p.equity == 15_000.0
