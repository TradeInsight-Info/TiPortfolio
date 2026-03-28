from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from tiportfolio.algo import Algo, AlgoQueue, Context
from tiportfolio.config import TiConfig


# ---------------------------------------------------------------------------
# Concrete test algos
# ---------------------------------------------------------------------------

class AlwaysTrue(Algo):
    def __call__(self, context: Context) -> bool:
        return True


class AlwaysFalse(Algo):
    def __call__(self, context: Context) -> bool:
        return False


class RecordingAlgo(Algo):
    """Records whether it was called."""
    def __init__(self) -> None:
        self.called = False

    def __call__(self, context: Context) -> bool:
        self.called = True
        return True


# ---------------------------------------------------------------------------
# Context tests
# ---------------------------------------------------------------------------

class TestContext:
    def _make_context(self) -> Context:
        portfolio = MagicMock()
        portfolio.name = "test"
        prices: dict[str, pd.DataFrame] = {}
        date = pd.Timestamp("2024-01-02", tz="UTC")
        config = TiConfig()
        return Context(
            portfolio=portfolio,
            prices=prices,
            date=date,
            config=config,
        )

    def test_selected_defaults_empty(self) -> None:
        ctx = self._make_context()
        assert ctx.selected == []

    def test_weights_defaults_empty(self) -> None:
        ctx = self._make_context()
        assert ctx.weights == {}

    def test_callbacks_default_none(self) -> None:
        ctx = self._make_context()
        assert ctx._execute_leaf is None
        assert ctx._allocate_children is None

    def test_mutable_selected(self) -> None:
        ctx = self._make_context()
        ctx.selected = ["QQQ", "BIL"]
        assert ctx.selected == ["QQQ", "BIL"]

    def test_mutable_weights(self) -> None:
        ctx = self._make_context()
        ctx.weights = {"QQQ": 0.5, "BIL": 0.5}
        assert ctx.weights == {"QQQ": 0.5, "BIL": 0.5}


# ---------------------------------------------------------------------------
# Algo ABC tests
# ---------------------------------------------------------------------------

class TestAlgoABC:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            Algo()  # type: ignore[abstract]

    def test_concrete_subclass_works(self) -> None:
        algo = AlwaysTrue()
        ctx = MagicMock()
        assert algo(ctx) is True


# ---------------------------------------------------------------------------
# AlgoQueue tests
# ---------------------------------------------------------------------------

class TestAlgoQueue:
    def test_all_true_returns_true(self) -> None:
        queue = AlgoQueue([AlwaysTrue(), AlwaysTrue(), AlwaysTrue()])
        ctx = MagicMock()
        assert queue(ctx) is True

    def test_all_false_returns_false(self) -> None:
        queue = AlgoQueue([AlwaysFalse()])
        ctx = MagicMock()
        assert queue(ctx) is False

    def test_short_circuits_on_false(self) -> None:
        a1 = RecordingAlgo()
        a2 = AlwaysFalse()
        a3 = RecordingAlgo()
        queue = AlgoQueue([a1, a2, a3])
        ctx = MagicMock()
        result = queue(ctx)
        assert result is False
        assert a1.called is True
        assert a3.called is False  # never reached

    def test_empty_queue_returns_true(self) -> None:
        queue = AlgoQueue([])
        ctx = MagicMock()
        assert queue(ctx) is True

    def test_queue_is_algo_subclass(self) -> None:
        queue = AlgoQueue([])
        assert isinstance(queue, Algo)
