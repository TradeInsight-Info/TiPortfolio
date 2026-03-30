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


# ---------------------------------------------------------------------------
# Ratio
# ---------------------------------------------------------------------------


class TestWeighRatio:
    def test_already_summing_to_one(self) -> None:
        ctx = _make_context(["QQQ", "BIL", "GLD"])
        algo = Weigh.Ratio(weights={"QQQ": 0.6, "BIL": 0.3, "GLD": 0.1})
        assert algo(ctx) is True
        assert ctx.weights == pytest.approx({"QQQ": 0.6, "BIL": 0.3, "GLD": 0.1})

    def test_normalises_non_unit_weights(self) -> None:
        ctx = _make_context(["A", "B"])
        Weigh.Ratio(weights={"A": 3.0, "B": 1.0})(ctx)
        assert ctx.weights == pytest.approx({"A": 0.75, "B": 0.25})

    def test_missing_ticker_excluded(self) -> None:
        ctx = _make_context(["QQQ", "BIL", "GLD"])
        Weigh.Ratio(weights={"QQQ": 0.7, "GLD": 0.3})(ctx)
        # BIL is selected but not in weights — excluded (position closed)
        assert "BIL" not in ctx.weights
        assert ctx.weights == pytest.approx({"QQQ": 0.7, "GLD": 0.3})

    def test_returns_true(self) -> None:
        ctx = _make_context(["A"])
        assert Weigh.Ratio(weights={"A": 1.0})(ctx) is True


# ---------------------------------------------------------------------------
# BasedOnHV
# ---------------------------------------------------------------------------


def _make_price_df(prices: list[float]) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=len(prices), freq="B")
    dates = dates.tz_localize("UTC")
    return pd.DataFrame({"close": prices}, index=dates)


def _make_hv_context(
    prices: dict[str, pd.DataFrame],
    selected: list[str],
    date: str = "2024-01-31",
    bars_per_year: int = 252,
) -> Context:
    portfolio = MagicMock()
    portfolio.name = "test"
    ctx = Context(
        portfolio=portfolio,
        prices=prices,
        date=pd.Timestamp(date, tz="UTC"),
        config=TiConfig(bars_per_year=bars_per_year),
    )
    ctx.selected = selected
    return ctx


class TestWeighBasedOnHV:
    def test_scales_down_high_vol(self) -> None:
        # Create prices with known volatility
        prices = {
            "A": _make_price_df([100 + i * 2 for i in range(20)]),
            "B": _make_price_df([50 + i * 0.5 for i in range(20)]),
        }
        ctx = _make_hv_context(prices, ["A", "B"])
        algo = Weigh.BasedOnHV(
            initial_ratio={"A": 0.7, "B": 0.3},
            target_hv=0.01,  # very low target
            lookback=pd.DateOffset(days=30),
        )
        assert algo(ctx) is True
        # Weights should be scaled down (sum < 1)
        total_weight = sum(ctx.weights.values())
        assert total_weight < 1.0

    def test_scales_up_low_vol(self) -> None:
        # Very low volatility prices
        prices = {
            "A": _make_price_df([100.0 + i * 0.01 for i in range(20)]),
            "B": _make_price_df([50.0 + i * 0.005 for i in range(20)]),
        }
        ctx = _make_hv_context(prices, ["A", "B"])
        algo = Weigh.BasedOnHV(
            initial_ratio={"A": 0.5, "B": 0.5},
            target_hv=0.50,  # high target
            lookback=pd.DateOffset(days=30),
        )
        algo(ctx)
        # Weights should be scaled up (sum > 1 = leverage)
        total_weight = sum(ctx.weights.values())
        assert total_weight > 1.0

    def test_zero_vol_returns_initial_ratio(self) -> None:
        # All flat prices → zero volatility
        prices = {
            "A": _make_price_df([100.0] * 20),
            "B": _make_price_df([50.0] * 20),
        }
        ctx = _make_hv_context(prices, ["A", "B"])
        algo = Weigh.BasedOnHV(
            initial_ratio={"A": 0.6, "B": 0.4},
            target_hv=0.15,
            lookback=pd.DateOffset(days=30),
        )
        algo(ctx)
        assert ctx.weights == pytest.approx({"A": 0.6, "B": 0.4})

    def test_returns_true(self) -> None:
        prices = {"A": _make_price_df([100.0] * 5)}
        ctx = _make_hv_context(prices, ["A"], date="2024-01-08")
        algo = Weigh.BasedOnHV(
            initial_ratio={"A": 1.0},
            target_hv=0.15,
            lookback=pd.DateOffset(days=10),
        )
        assert algo(ctx) is True
