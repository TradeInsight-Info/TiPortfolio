from pathlib import Path
from unittest import TestCase

import pandas as pd

from tiportfolio.portfolio.allocation.allocation import PortfolioConfig
from tiportfolio.portfolio.allocation.frequency_based_allocation import RebalanceFrequency
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.strategy_library.allocation.fix_percentage import (
    FixPercentageFrequencyBasedAllocation,
)
from tiportfolio.strategy_library.trading.long_hold import LongHold


class TestFixPercentageAllocationAllApple(TestCase):
    def setUp(self) -> None:
        data_path = Path(__file__).resolve().parents[1] / "data" / "aapl.csv"
        df = pd.read_csv(data_path, parse_dates=["date"])
        df.set_index("date", inplace=True)
        self.prices = df[["open", "high", "low", "close", "volume"]]

        fees: FeesConfig = {
            "commission": 0.0001,
            "slippage": 0.0,
        }
        self.config: PortfolioConfig = {
            "fees_config": fees,
            "risk_free_rate": 0.04,
            "initial_capital": 100_000,
            "market_name": "NYSE",
        }

        self.strategy = LongHold(
            symbol="AAPL",
            prices=self.prices.copy(),
        )

    def test_allocation_runs_full_history(self) -> None:
        allocation = FixPercentageFrequencyBasedAllocation(
            config=self.config,
            strategies=[self.strategy],
            allocation_percentages=[1.0],
            rebalance_frequency=RebalanceFrequency.daily,
            market_name="NYSE",
        )

        allocation.walk_forward()

        self.assertFalse(allocation.portfolio_df.empty)
        self.assertEqual(
            allocation.portfolio_df.index.names,
            ["datetime", "strategy_unique_name"],
        )
        self.assertIn("signal", allocation.portfolio_df.columns)
        self.assertEqual(
            len(allocation.portfolio_df),
            len(self.strategy.prices_df),
        )
