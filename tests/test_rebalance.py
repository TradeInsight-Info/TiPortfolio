from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from tiportfolio.algo import Context
from tiportfolio.algos.rebalance import Action
from tiportfolio.config import TiConfig
from tiportfolio.portfolio import Portfolio


def _make_leaf_context(callback: object | None = None) -> Context:
    portfolio = Portfolio("test", [], ["QQQ", "BIL"])
    return Context(
        portfolio=portfolio,
        prices={},
        date=pd.Timestamp("2024-01-02", tz="UTC"),
        config=TiConfig(),
        _execute_leaf=callback,  # type: ignore[arg-type]
    )


class TestActionRebalance:
    def test_calls_execute_leaf_for_leaf(self) -> None:
        cb = MagicMock()
        ctx = _make_leaf_context(callback=cb)
        algo = Action.Rebalance()
        result = algo(ctx)
        assert result is True
        cb.assert_called_once_with(ctx.portfolio, ctx)

    def test_raises_if_callback_none(self) -> None:
        ctx = _make_leaf_context(callback=None)
        with pytest.raises(RuntimeError, match="callback"):
            Action.Rebalance()(ctx)

    def test_returns_true(self) -> None:
        cb = MagicMock()
        ctx = _make_leaf_context(callback=cb)
        assert Action.Rebalance()(ctx) is True


class TestActionPrintInfo:
    def test_returns_true(self) -> None:
        portfolio = Portfolio("test", [], ["QQQ"])
        ctx = Context(
            portfolio=portfolio,
            prices={},
            date=pd.Timestamp("2024-01-31", tz="UTC"),
            config=TiConfig(),
        )
        assert Action.PrintInfo()(ctx) is True

    def test_prints_debug(self, capsys: pytest.CaptureFixture[str]) -> None:
        portfolio = Portfolio("myport", [], ["QQQ"])
        ctx = Context(
            portfolio=portfolio,
            prices={},
            date=pd.Timestamp("2024-01-31", tz="UTC"),
            config=TiConfig(),
        )
        Action.PrintInfo()(ctx)
        captured = capsys.readouterr()
        assert "2024-01-31" in captured.out
        assert "myport" in captured.out
