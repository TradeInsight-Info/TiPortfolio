from datetime import datetime, timedelta
from unittest import TestCase

import pandas as pd

from tiportfolio.strategies.allocation.half import FixedAllocation50_50
from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm
from tiportfolio.portfolio.types import TradingSignal


class DummyTradingAlgorithm(TradingAlgorithm[dict]):
    """Simple strategy that always returns a fixed signal.

    Signals are not used by FixedAllocation50_50 but are required to
    exercise the public allocation API (walk_forward).
    """

    def __init__(self, signal: TradingSignal = TradingSignal.LONG) -> None:
        super().__init__(name="dummy")
        self._signal = signal

    def _run(self, history_data: dict) -> TradingSignal:  # type: ignore[override]
        return self._signal


class TestFixedAllocation50_50(TestCase):

    def _build_prices(self) -> pd.DataFrame:
        """Build a simple daily price series spanning multiple months.

        The first asset will drift upward more strongly than the second so
        that, by the start of a new month, it becomes overweight relative to
        50% of the total portfolio value.
        """

        dates = pd.date_range(start="2024-01-25", end="2024-03-10", freq="D")

        # Strong uptrend for asset A, mild uptrend for asset B.
        base = 100.0
        a_close = [base + i * 2.0 for i in range(len(dates))]
        b_close = [base + i * 0.5 for i in range(len(dates))]

        def _df_from_close(close: list[float]) -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "open": close,
                    "high": [c * 1.01 for c in close],
                    "low": [c * 0.99 for c in close],
                    "close": close,
                    "volume": [100 + i for i in range(len(close))],
                },
                index=dates,
            )

        return _df_from_close(a_close), _df_from_close(b_close)

    def _build_config(self) -> dict:
        return {
            "fees_config": {"commission": 0.0, "slippage": 0.0, "risk_free_rate": 0.0},
            "initial_capital": 100_000.0,
            "time_start": datetime(2024, 1, 25),
            "time_end": datetime(2024, 3, 10),
            "timeframe": timedelta(days=1),
        }

    def test_requires_exactly_two_assets(self) -> None:
        prices_a, _ = self._build_prices()
        history_a = {"prices": prices_a}

        config = self._build_config()
        strategy = DummyTradingAlgorithm()

        # Only one asset -> should raise ValueError
        with self.assertRaises(ValueError):
            FixedAllocation50_50(config, [("A", history_a, strategy)])

    def test_walk_forward_returns_50_50_weights(self) -> None:
        prices_a, prices_b = self._build_prices()
        history_a = {"prices": prices_a}
        history_b = {"prices": prices_b}

        config = self._build_config()
        strat_a = DummyTradingAlgorithm()
        strat_b = DummyTradingAlgorithm()

        alloc = FixedAllocation50_50(
            config,
            [
                ("A", history_a, strat_a),
                ("B", history_b, strat_b),
            ],
        )

        portfolio_history = alloc.walk_forward()

        # Basic structure checks
        self.assertIsInstance(portfolio_history, list)
        self.assertGreater(len(portfolio_history), 0)

        required_keys = {
            "datetime",
            "symbol",
            "signal",
            "price",
            "value",
            "quantity",
            "fee_amount",
            "avg_cost",
            "unrealised_pnl",
        }

        for record in portfolio_history:
            self.assertTrue(required_keys.issubset(record.keys()))

        # Every step should have 50/50 target weights when aggregated per datetime
        # using the notional values implied by the allocation engine.
        by_datetime: dict = {}
        for record in portfolio_history:
            dt = record["datetime"]
            by_datetime.setdefault(dt, {})[record["symbol"]] = record["value"]

        for values in by_datetime.values():
            total = sum(values.values())
            if total == 0:
                continue
            weight_a = values["A"] / total
            weight_b = values["B"] / total
            self.assertAlmostEqual(weight_a, 0.5, places=6)
            self.assertAlmostEqual(weight_b, 0.5, places=6)

    def test_monthly_rebalance_when_overweight(self) -> None:
        prices_a, prices_b = self._build_prices()
        history_a = {"prices": prices_a}
        history_b = {"prices": prices_b}

        config = self._build_config()
        strat_a = DummyTradingAlgorithm()
        strat_b = DummyTradingAlgorithm()

        alloc = FixedAllocation50_50(
            config,
            [
                ("A", history_a, strat_a),
                ("B", history_b, strat_b),
            ],
        )

        # Manually step through dates to control when we inspect state.
        dates = prices_a.index

        # Run through all dates up to the end of January to let A become
        # overweight due to its stronger uptrend.
        jan_end = datetime(2024, 1, 31)
        for ts in dates[dates <= pd.Timestamp(jan_end)]:
            alloc.optimize_portfolio(ts.to_pydatetime(), signals={})

        # At the end of January we expect asset A to be overweight
        total_before = sum(alloc._current_values.values())
        weight_a_before = alloc._current_values["A"] / total_before
        self.assertGreater(weight_a_before, 0.5)

        # First trading day of February should trigger a rebalance
        feb_first = datetime(2024, 2, 1)
        alloc.optimize_portfolio(feb_first, signals={})

        # After rebalance, notional values should be equal 50/50
        self.assertAlmostEqual(
            alloc._current_values["A"], alloc._current_values["B"], places=6
        )
