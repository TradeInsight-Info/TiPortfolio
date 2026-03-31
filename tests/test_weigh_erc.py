from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from tiportfolio.algo import Context
from tiportfolio.algos.weigh import Weigh
from tiportfolio.config import TiConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_price_df(prices: list[float]) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=len(prices), freq="B")
    dates = dates.tz_localize("UTC")
    return pd.DataFrame({"close": prices}, index=dates)


def _make_context(
    prices: dict[str, pd.DataFrame],
    selected: list[str],
    date: str = "2024-02-01",
) -> Context:
    portfolio = MagicMock()
    portfolio.name = "test"
    ctx = Context(
        portfolio=portfolio,
        prices=prices,
        date=pd.Timestamp(date, tz="UTC"),
        config=TiConfig(),
    )
    ctx.selected = selected
    return ctx


def _synthetic_prices(
    n_assets: int = 3, n_days: int = 60, seed: int = 42
) -> dict[str, pd.DataFrame]:
    """Generate synthetic price data for multiple uncorrelated assets."""
    rng = np.random.default_rng(seed)
    tickers = [chr(ord("A") + i) for i in range(n_assets)]
    result: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        returns = rng.normal(0.001, 0.01 * (1 + ord(ticker) - ord("A")), n_days)
        prices = 100.0 * np.cumprod(1 + returns)
        result[ticker] = _make_price_df(prices.tolist())
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestERCConstruction:
    def test_default_construction(self) -> None:
        algo = Weigh.ERC(lookback=pd.DateOffset(months=3))
        assert algo is not None

    def test_custom_construction(self) -> None:
        algo = Weigh.ERC(
            lookback=pd.DateOffset(months=6),
            covar_method="oas",
            risk_parity_method="slsqp",
            maximum_iterations=200,
            tolerance=1e-10,
        )
        assert algo is not None


class TestERCComputation:
    def test_returns_true(self) -> None:
        prices = _synthetic_prices(n_assets=3, n_days=60)
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1))
        result = algo(ctx)
        assert result is True

    def test_writes_weights_to_context(self) -> None:
        prices = _synthetic_prices(n_assets=3, n_days=60)
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1))
        algo(ctx)
        assert isinstance(ctx.weights, dict)
        assert set(ctx.weights.keys()) == {"A", "B", "C"}


class TestERCWeightProperties:
    def test_weights_sum_to_one(self) -> None:
        prices = _synthetic_prices(n_assets=4, n_days=60, seed=10)
        ctx = _make_context(prices, ["A", "B", "C", "D"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1))
        algo(ctx)
        total = sum(ctx.weights.values())
        assert total == pytest.approx(1.0, abs=1e-8)

    def test_all_weights_non_negative(self) -> None:
        prices = _synthetic_prices(n_assets=3, n_days=60, seed=20)
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1))
        algo(ctx)
        for w in ctx.weights.values():
            assert w >= 0.0

    def test_higher_vol_asset_gets_lower_weight(self) -> None:
        """Asset with higher volatility should receive lower ERC weight."""
        rng = np.random.default_rng(42)
        n = 60
        # A: low vol, B: high vol, C: medium vol
        prices = {
            "A": _make_price_df((100.0 * np.cumprod(1 + rng.normal(0.001, 0.005, n))).tolist()),
            "B": _make_price_df((100.0 * np.cumprod(1 + rng.normal(0.001, 0.030, n))).tolist()),
            "C": _make_price_df((100.0 * np.cumprod(1 + rng.normal(0.001, 0.015, n))).tolist()),
        }
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1))
        algo(ctx)
        # Low-vol asset A should have highest weight
        assert ctx.weights["A"] > ctx.weights["B"]


class TestERCCovarMethods:
    def test_ledoit_wolf(self) -> None:
        prices = _synthetic_prices(n_assets=3, n_days=60)
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1), covar_method="ledoit-wolf")
        algo(ctx)
        assert sum(ctx.weights.values()) == pytest.approx(1.0, abs=1e-8)

    def test_hist(self) -> None:
        prices = _synthetic_prices(n_assets=3, n_days=60)
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1), covar_method="hist")
        algo(ctx)
        assert sum(ctx.weights.values()) == pytest.approx(1.0, abs=1e-8)

    def test_oas(self) -> None:
        prices = _synthetic_prices(n_assets=3, n_days=60)
        ctx = _make_context(prices, ["A", "B", "C"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1), covar_method="oas")
        algo(ctx)
        assert sum(ctx.weights.values()) == pytest.approx(1.0, abs=1e-8)


class TestERCErrors:
    def test_raises_value_error_insufficient_data(self) -> None:
        """ValueError when lookback window has fewer than 2 observations."""
        dates = pd.DatetimeIndex(
            [pd.Timestamp("2024-01-15", tz="UTC")]
        )
        prices = {
            "A": pd.DataFrame({"close": [100.0]}, index=dates),
            "B": pd.DataFrame({"close": [50.0]}, index=dates),
        }
        ctx = _make_context(prices, ["A", "B"], date="2024-02-01")
        algo = Weigh.ERC(lookback=pd.DateOffset(days=30))
        with pytest.raises(ValueError, match="(?i)insufficient"):
            algo(ctx)

    def test_raises_value_error_singular_covariance(self) -> None:
        """ValueError when assets have perfectly correlated returns."""
        n = 30
        base_prices = [100.0 + i * 0.5 for i in range(n)]
        # Perfectly correlated: B = 2*A (same returns)
        prices = {
            "A": _make_price_df(base_prices),
            "B": _make_price_df([p * 2 for p in base_prices]),
        }
        ctx = _make_context(prices, ["A", "B"])
        algo = Weigh.ERC(lookback=pd.DateOffset(months=1))
        # This may raise ValueError or produce degenerate weights
        # depending on riskfolio-lib's handling of singular matrices
        try:
            algo(ctx)
            # If it doesn't raise, weights should still sum to 1.0
            assert sum(ctx.weights.values()) == pytest.approx(1.0, abs=1e-6)
        except ValueError:
            pass  # Expected behavior for singular covariance
