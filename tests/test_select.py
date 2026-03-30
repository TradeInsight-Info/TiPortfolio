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


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------


def _make_price_df(prices: list[float]) -> pd.DataFrame:
    """Create a simple DataFrame with close prices over consecutive business days."""
    dates = pd.bdate_range("2024-01-02", periods=len(prices), freq="B")
    dates = dates.tz_localize("UTC")
    return pd.DataFrame({"close": prices}, index=dates)


class TestSelectMomentum:
    def test_selects_top_2_of_3(self) -> None:
        # QQQ rises a lot, GLD rises a bit, BIL is flat
        prices = {
            "QQQ": _make_price_df([100, 105, 110, 115, 120]),
            "GLD": _make_price_df([100, 101, 102, 103, 104]),
            "BIL": _make_price_df([100, 100, 100, 100, 100]),
        }
        portfolio = MagicMock()
        portfolio.name = "test"
        portfolio.children = ["QQQ", "GLD", "BIL"]
        ctx = Context(
            portfolio=portfolio,
            prices=prices,
            date=pd.Timestamp("2024-01-08", tz="UTC"),
            config=TiConfig(),
            selected=["QQQ", "GLD", "BIL"],
        )
        algo = Select.Momentum(n=2, lookback=pd.DateOffset(days=5), lag=pd.DateOffset(days=0))
        assert algo(ctx) is True
        assert ctx.selected == ["QQQ", "GLD"]

    def test_sort_ascending_selects_worst(self) -> None:
        prices = {
            "QQQ": _make_price_df([100, 105, 110, 115, 120]),
            "BIL": _make_price_df([100, 100, 100, 100, 100]),
        }
        portfolio = MagicMock()
        portfolio.name = "test"
        portfolio.children = ["QQQ", "BIL"]
        ctx = Context(
            portfolio=portfolio,
            prices=prices,
            date=pd.Timestamp("2024-01-08", tz="UTC"),
            config=TiConfig(),
            selected=["QQQ", "BIL"],
        )
        algo = Select.Momentum(n=1, lookback=pd.DateOffset(days=5), lag=pd.DateOffset(days=0), sort_descending=False)
        algo(ctx)
        assert ctx.selected == ["BIL"]

    def test_always_returns_true(self) -> None:
        prices = {"A": _make_price_df([100, 101])}
        portfolio = MagicMock()
        portfolio.name = "test"
        portfolio.children = ["A"]
        ctx = Context(
            portfolio=portfolio,
            prices=prices,
            date=pd.Timestamp("2024-01-03", tz="UTC"),
            config=TiConfig(),
            selected=["A"],
        )
        assert Select.Momentum(n=1, lookback=pd.DateOffset(days=2), lag=pd.DateOffset(days=0))(ctx) is True


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


class TestSelectFilter:
    def test_passes_when_condition_true(self) -> None:
        vix_df = pd.DataFrame(
            {"close": [25.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-02", tz="UTC")]),
        )
        algo = Select.Filter(
            data={"^VIX": vix_df},
            condition=lambda row: row["^VIX"]["close"] < 30,
        )
        ctx = _make_context(["QQQ"])
        ctx.selected = ["QQQ"]
        assert algo(ctx) is True

    def test_halts_when_condition_false(self) -> None:
        vix_df = pd.DataFrame(
            {"close": [35.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-02", tz="UTC")]),
        )
        algo = Select.Filter(
            data={"^VIX": vix_df},
            condition=lambda row: row["^VIX"]["close"] < 30,
        )
        ctx = _make_context(["QQQ"])
        ctx.selected = ["QQQ"]
        assert algo(ctx) is False

    def test_does_not_modify_selected(self) -> None:
        vix_df = pd.DataFrame(
            {"close": [25.0]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-02", tz="UTC")]),
        )
        algo = Select.Filter(
            data={"^VIX": vix_df},
            condition=lambda row: row["^VIX"]["close"] < 30,
        )
        ctx = _make_context(["QQQ", "BIL"])
        ctx.selected = ["QQQ", "BIL"]
        algo(ctx)
        assert ctx.selected == ["QQQ", "BIL"]
