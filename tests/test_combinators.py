from __future__ import annotations

import pytest

from tiportfolio.algo import Algo, And, Context, Not, Or
from tiportfolio.config import TiConfig


# ---------------------------------------------------------------------------
# Helpers — trivial algos that record whether they were called
# ---------------------------------------------------------------------------


class _AlwaysTrue(Algo):
    def __init__(self) -> None:
        self.called = False

    def __call__(self, context: Context) -> bool:
        self.called = True
        return True


class _AlwaysFalse(Algo):
    def __init__(self) -> None:
        self.called = False

    def __call__(self, context: Context) -> bool:
        self.called = True
        return False


@pytest.fixture()
def ctx() -> Context:
    from tiportfolio.portfolio import Portfolio

    p = Portfolio("test", [], ["A"])
    return Context(portfolio=p, prices={}, date=None, config=TiConfig())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Or
# ---------------------------------------------------------------------------


class TestOr:
    def test_all_false(self, ctx: Context) -> None:
        a, b = _AlwaysFalse(), _AlwaysFalse()
        assert Or(a, b)(ctx) is False
        assert a.called and b.called

    def test_first_true_short_circuits(self, ctx: Context) -> None:
        a, b = _AlwaysTrue(), _AlwaysFalse()
        assert Or(a, b)(ctx) is True
        assert a.called
        assert not b.called  # short-circuited

    def test_second_true(self, ctx: Context) -> None:
        a, b = _AlwaysFalse(), _AlwaysTrue()
        assert Or(a, b)(ctx) is True
        assert a.called and b.called

    def test_is_algo_subclass(self) -> None:
        assert issubclass(Or, Algo)


# ---------------------------------------------------------------------------
# And
# ---------------------------------------------------------------------------


class TestAnd:
    def test_all_true(self, ctx: Context) -> None:
        a, b = _AlwaysTrue(), _AlwaysTrue()
        assert And(a, b)(ctx) is True
        assert a.called and b.called

    def test_first_false_short_circuits(self, ctx: Context) -> None:
        a, b = _AlwaysFalse(), _AlwaysTrue()
        assert And(a, b)(ctx) is False
        assert a.called
        assert not b.called  # short-circuited

    def test_second_false(self, ctx: Context) -> None:
        a, b = _AlwaysTrue(), _AlwaysFalse()
        assert And(a, b)(ctx) is False
        assert a.called and b.called

    def test_is_algo_subclass(self) -> None:
        assert issubclass(And, Algo)


# ---------------------------------------------------------------------------
# Not
# ---------------------------------------------------------------------------


class TestNot:
    def test_inverts_true(self, ctx: Context) -> None:
        a = _AlwaysTrue()
        assert Not(a)(ctx) is False
        assert a.called

    def test_inverts_false(self, ctx: Context) -> None:
        a = _AlwaysFalse()
        assert Not(a)(ctx) is True
        assert a.called

    def test_is_algo_subclass(self) -> None:
        assert issubclass(Not, Algo)


# ---------------------------------------------------------------------------
# Nesting
# ---------------------------------------------------------------------------


class TestNesting:
    def test_or_and_not_composition(self, ctx: Context) -> None:
        """Or(And(True, False), Not(False)) → Or(False, True) → True"""
        result = Or(And(_AlwaysTrue(), _AlwaysFalse()), Not(_AlwaysFalse()))(ctx)
        assert result is True

    def test_and_or_not_composition(self, ctx: Context) -> None:
        """And(Or(False, True), Not(True)) → And(True, False) → False"""
        result = And(Or(_AlwaysFalse(), _AlwaysTrue()), Not(_AlwaysTrue()))(ctx)
        assert result is False
