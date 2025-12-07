from pathlib import Path
from unittest import TestCase

import pandas as pd

from tiportfolio.portfolio.allocation.allocation import PortfolioConfig
from tiportfolio.portfolio.allocation.frequency_based_allocation import RebalanceFrequency
from tiportfolio.portfolio.types import FeesConfig
from tiportfolio.strategy_library.allocation.fix_ratio import (
    FixRatioFrequencyBasedAllocation,
)
from tiportfolio.strategy_library.trading.long_hold import LongHold


class TestFixRatioAllocationAllApple(TestCase):
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
        allocation = FixRatioFrequencyBasedAllocation(
            config=self.config,
            strategies=[self.strategy],
            allocation_ratio_list=[1.0],
            rebalance_frequency=RebalanceFrequency.mid_of_month,
            market_name="NYSE",
        )

        allocation.walk_forward()
        strategy_quantity_map = allocation.strategy_ratio_map

        # all step should be in middle of month
        """Sample Response
        
        {(Timestamp('2019-01-15 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-02-15 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-03-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-04-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-05-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-06-17 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-07-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-08-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-09-16 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-10-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-11-15 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2019-12-16 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-01-15 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-02-18 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-03-16 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-04-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-05-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-06-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-07-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-08-17 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-09-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-10-15 09:30:00-0400', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-11-16 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0, (Timestamp('2020-12-15 09:30:00-0500', tz='America/New_York'), 'LongHold - AAPL'): 1.0}

        """
        # in the strategy_quantity_map, the key should be match the list above
        for (step, strategy_name), allocation_percentage in strategy_quantity_map.items():
            self.assertEqual(strategy_name, "LongHold - AAPL")
            self.assertEqual(allocation_percentage, 1.0)


        # get list of steps
        rebalance_dates = map(
            lambda x: x[0],
            strategy_quantity_map.keys(),
        )

        self.assertListEqual(
            list(rebalance_dates),
            [
                pd.Timestamp("2019-01-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-02-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-03-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-04-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-05-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-06-17 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-07-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-08-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-09-16 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-10-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2019-11-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-12-16 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2020-01-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2020-02-18 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2020-03-16 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-04-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-05-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-06-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-07-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-08-17 09:30:00-04:00", tz="America/New_York"),
                # until december 2020
                pd.Timestamp("2020-09-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-10-15 09:30:00-04:00", tz="America/New_York"),
                pd.Timestamp("2020-11-16 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2020-12-15 09:30:00-05:00", tz="America/New_York"),
        ]
        )
