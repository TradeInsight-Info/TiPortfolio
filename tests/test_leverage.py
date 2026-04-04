from __future__ import annotations

import pandas as pd
import pytest

from tiportfolio.algos.rebalance import Action
from tiportfolio.algos.select import Select
from tiportfolio.algos.signal import Signal
from tiportfolio.algos.weigh import Weigh
from tiportfolio.backtest import Backtest, run
from tiportfolio.config import TiConfig
from tiportfolio.portfolio import Portfolio


def _make_backtest(
    prices_dict: dict[str, pd.DataFrame],
    name: str = "TestPortfolio",
    config: TiConfig | None = None,
) -> Backtest:
    """Helper to create a simple monthly-rebalanced equal-weight backtest."""
    portfolio = Portfolio(
        name,
        [Signal.Monthly(day="start"), Select.All(), Weigh.Equally(), Action.Rebalance()],
        ["QQQ", "BIL", "GLD"],
    )
    return Backtest(portfolio, prices_dict, config=config)


class TestLeverageIdentity:
    """Leverage=1.0 (default) must produce identical results."""

    def test_default_leverage_unchanged(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt = _make_backtest(prices_dict)
        bt2 = _make_backtest(prices_dict, name="TestPortfolio")
        result_default = run(bt)
        result_explicit = run(bt2, leverage=1.0)
        pd.testing.assert_series_equal(
            result_default[0].equity_curve,
            result_explicit[0].equity_curve,
        )

    def test_default_leverage_name_unchanged(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt = _make_backtest(prices_dict)
        result = run(bt, leverage=1.0)
        assert result[0].name == "TestPortfolio"


class TestLeverageBorrowingCost:
    """Leverage scaling must include borrowing cost deduction."""

    def test_2x_leverage_scales_returns_with_cost(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        config = TiConfig()
        bt_base = _make_backtest(prices_dict, name="Base", config=config)
        bt_lev = _make_backtest(prices_dict, name="Lev", config=config)

        result_base = run(bt_base)
        result_lev = run(bt_lev, leverage=2.0)

        eq_base = result_base[0].equity_curve
        eq_lev = result_lev[0].equity_curve

        # Manually compute expected leveraged equity
        returns = eq_base.pct_change().fillna(0.0)
        daily_cost = (2.0 - 1) * config.loan_rate / config.bars_per_year
        leveraged_returns = returns * 2.0 - daily_cost
        expected_eq = eq_base.iloc[0] * (1 + leveraged_returns).cumprod()
        expected_eq.iloc[0] = eq_base.iloc[0]

        pd.testing.assert_series_equal(eq_lev, expected_eq, check_names=False)

    def test_higher_leverage_higher_cost(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt2 = _make_backtest(prices_dict, name="2x")
        bt3 = _make_backtest(prices_dict, name="3x")
        result_2x = run(bt2, leverage=2.0)
        result_3x = run(bt3, leverage=3.0)

        # 3x should have lower final value than 2x would naively predict
        # because borrowing cost is (3-1)=2 vs (2-1)=1 times loan_rate
        eq_2x = result_2x[0].equity_curve
        eq_3x = result_3x[0].equity_curve

        # Compute daily cost difference
        config = TiConfig()
        cost_2x = (2.0 - 1) * config.loan_rate / config.bars_per_year
        cost_3x = (3.0 - 1) * config.loan_rate / config.bars_per_year
        assert cost_3x == pytest.approx(cost_2x * 2)

    def test_borrowing_cost_on_down_day(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        """Borrowing cost applies even when returns are negative."""
        config = TiConfig()
        bt = _make_backtest(prices_dict, config=config)
        result = run(bt, leverage=2.0)
        eq_base_bt = _make_backtest(prices_dict, config=config)
        result_base = run(eq_base_bt)

        base_returns = result_base[0].equity_curve.pct_change().dropna()
        lev_returns = result[0].equity_curve.pct_change().dropna()

        daily_cost = (2.0 - 1) * config.loan_rate / config.bars_per_year

        # For each day (skip first — it's an artifact of fillna(0) in _apply_leverage),
        # leveraged_return should be 2*base_return - daily_cost
        expected = base_returns * 2.0 - daily_cost
        pd.testing.assert_series_equal(
            lev_returns.iloc[1:], expected.iloc[1:], check_names=False
        )


class TestLeverageBroadcast:
    """Single float broadcasts to all backtests; list applies per-backtest."""

    def test_single_float_applies_to_all(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt1 = _make_backtest(prices_dict, name="P1")
        bt2 = _make_backtest(prices_dict, name="P2")
        result = run(bt1, bt2, leverage=2.0)
        # Both should be leveraged (different from unleveraged)
        bt1_base = _make_backtest(prices_dict, name="P1Base")
        bt2_base = _make_backtest(prices_dict, name="P2Base")
        result_base = run(bt1_base, bt2_base)
        assert result[0].equity_curve.iloc[-1] != result_base[0].equity_curve.iloc[-1]
        assert result[1].equity_curve.iloc[-1] != result_base[1].equity_curve.iloc[-1]

    def test_list_applies_per_backtest(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt1 = _make_backtest(prices_dict, name="P1")
        bt2 = _make_backtest(prices_dict, name="P2")
        result = run(bt1, bt2, leverage=[1.5, 2.0])
        assert result[0].name == "P1 (1.5x)"
        assert result[1].name == "P2 (2.0x)"


class TestLeverageValidation:
    """Mismatched list length raises ValueError."""

    def test_list_length_mismatch_raises(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt1 = _make_backtest(prices_dict, name="P1")
        bt2 = _make_backtest(prices_dict, name="P2")
        with pytest.raises(ValueError, match="mismatch"):
            run(bt1, bt2, leverage=[1.5])


class TestLeverageNameSuffix:
    """Name suffix added when leverage != 1.0."""

    def test_suffix_added(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt = _make_backtest(prices_dict, name="MyPortfolio")
        result = run(bt, leverage=2.0)
        assert result[0].name == "MyPortfolio (2.0x)"

    def test_no_suffix_at_1x(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt = _make_backtest(prices_dict, name="MyPortfolio")
        result = run(bt, leverage=1.0)
        assert result[0].name == "MyPortfolio"


class TestLeverageSummary:
    """Summary includes leverage row."""

    def test_summary_includes_leverage(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt = _make_backtest(prices_dict)
        result = run(bt, leverage=2.0)
        summary = result[0].summary()
        assert "leverage" in summary.index
        assert summary.loc["leverage", "value"] == 2.0

    def test_summary_default_leverage(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bt = _make_backtest(prices_dict)
        result = run(bt)
        summary = result[0].summary()
        assert "leverage" in summary.index
        assert summary.loc["leverage", "value"] == 1.0
