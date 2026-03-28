from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from tiportfolio.algo import Context
from tiportfolio.algos.select import Select
from tiportfolio.config import TiConfig


def _make_context(children: list) -> Context:
    portfolio = MagicMock()
    portfolio.name = "test"
    portfolio.children = children
    return Context(
        portfolio=portfolio,
        prices={},
        date=pd.Timestamp("2024-01-02", tz="UTC"),
        config=TiConfig(),
    )


class TestSelectAll:
    def test_populates_selected_from_children(self) -> None:
        ctx = _make_context(["QQQ", "BIL", "GLD"])
        algo = Select.All()
        result = algo(ctx)
        assert result is True
        assert ctx.selected == ["QQQ", "BIL", "GLD"]

    def test_returns_true(self) -> None:
        ctx = _make_context(["QQQ"])
        assert Select.All()(ctx) is True

    def test_none_children(self) -> None:
        ctx = _make_context(None)  # type: ignore[arg-type]
        ctx.portfolio.children = None
        Select.All()(ctx)
        assert ctx.selected == []

    def test_empty_children(self) -> None:
        ctx = _make_context([])
        Select.All()(ctx)
        assert ctx.selected == []
