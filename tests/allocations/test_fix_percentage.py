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
        df["date"] = (
            pd.to_datetime(df["date"], utc=True)
            .dt.tz_convert("America/New_York")
        )
        df.set_index("date", inplace=True)
        market_open_index = df.index.normalize() + pd.Timedelta(hours=9, minutes=30)
        market_open_index = market_open_index.tz_convert("America/New_York")
        df.index = market_open_index
        df.index.name = "date"
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
            stock_symbol="AAPL",
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

        print(allocation.strategy_quantity_map)
