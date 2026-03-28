from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from tiportfolio.algo import Context
from tiportfolio.algos.weigh import Weigh
from tiportfolio.config import TiConfig


def _make_context(selected: list) -> Context:
    portfolio = MagicMock()
    portfolio.name = "test"
    ctx = Context(
        portfolio=portfolio,
        prices={},
        date=pd.Timestamp("2024-01-02", tz="UTC"),
        config=TiConfig(),
    )
    ctx.selected = selected
    return ctx


class TestWeighEqually:
    def test_three_tickers(self) -> None:
        ctx = _make_context(["QQQ", "BIL", "GLD"])
        algo = Weigh.Equally()
        result = algo(ctx)
        assert result is True
        assert len(ctx.weights) == 3
        for w in ctx.weights.values():
            assert pytest.approx(w, abs=1e-10) == 1 / 3

    def test_two_tickers(self) -> None:
        ctx = _make_context(["QQQ", "BIL"])
        Weigh.Equally()(ctx)
        assert ctx.weights == pytest.approx({"QQQ": 0.5, "BIL": 0.5})

    def test_single_ticker(self) -> None:
        ctx = _make_context(["QQQ"])
        Weigh.Equally()(ctx)
        assert ctx.weights == {"QQQ": pytest.approx(1.0)}

    def test_returns_true(self) -> None:
        ctx = _make_context(["QQQ"])
        assert Weigh.Equally()(ctx) is True
