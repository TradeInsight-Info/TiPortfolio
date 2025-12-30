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

class TestFixRatioAllocationAllOnAppleFrom20190101to20190331(TestCase):
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

        # cut df to 2019-01-01 to 2019-03-31
        df = df.loc["2019-01-01":"2019-03-31"]  # type: ignore
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
        # in the strategy_quantity_map, the key should be match the list above and value should be 1.0 all the time
        for (step, strategy_name), allocation_percentage in strategy_quantity_map.items():
            self.assertEqual(strategy_name, "LongHold - AAPL")
            self.assertEqual(allocation_percentage, 1.0)


        # get list of steps
        rebalance_dates = map(
            lambda x: x[0],
            strategy_quantity_map.keys(),
        )

        # the step should be match the expected mid of month dates
        self.assertListEqual(
            list(rebalance_dates),
            [
                pd.Timestamp("2019-01-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-02-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-03-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-04-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-05-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-06-17 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-07-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-08-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-09-16 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-10-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2019-11-15 09:30:00-05:00", tz="America/New_York"),
                # pd.Timestamp("2019-12-16 09:30:00-05:00", tz="America/New_York"),
                # pd.Timestamp("2020-01-15 09:30:00-05:00", tz="America/New_York"),
                # pd.Timestamp("2020-02-18 09:30:00-05:00", tz="America/New_York"),
                # pd.Timestamp("2020-03-16 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-04-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-05-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-06-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-07-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-08-17 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-09-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-10-15 09:30:00-04:00", tz="America/New_York"),
                # pd.Timestamp("2020-11-16 09:30:00-05:00", tz="America/New_York"),
                # pd.Timestamp("2020-12-15 09:30:00-05:00", tz="America/New_York"),
        ])


        allocation.evaluate()
        self.assertFalse(allocation.portfolio_df.empty)

        print("Portfolio DataFrame top 16 and bottom 16 rows:")
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value' ]].head(20))
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value' ]].tail(20))





        print("Portfolio Result Metrics:")
        metrics = allocation.get_performance_metrics(True)
        print(metrics)


class TestFixRatioAllocationAllOnAppleAndGLDFrom20190101to20190331(TestCase):
    def setUp(self) -> None:
        # Load AAPL data
        appl_csv = Path(__file__).resolve().parents[1] / "data" / "aapl.csv"
        df_aapl = pd.read_csv(appl_csv, parse_dates=["date"])
        df_aapl["date"] = (
            pd.to_datetime(df_aapl["date"], utc=True)
            .dt.tz_convert("America/New_York")
        )
        df_aapl.set_index("date", inplace=True)
        market_open_index = df_aapl.index.normalize() + pd.Timedelta(hours=9, minutes=30)
        market_open_index = market_open_index.tz_convert("America/New_York")
        df_aapl.index = market_open_index
        df_aapl.index.name = "date"

        # cut df to 2019-01-01 to 2019-03-31
        df_aapl = df_aapl.loc["2019-01-01":"2019-03-31"]  # type: ignore
        self.prices_aapl = df_aapl[["open", "high", "low", "close", "volume"]]

        # Load GLD data (reuse same index since dates are the same)
        gld_csv = Path(__file__).resolve().parents[1] / "data" / "gld.csv"
        df_gld = pd.read_csv(gld_csv, parse_dates=["date"])
        df_gld["date"] = (
            pd.to_datetime(df_gld["date"], utc=True)
            .dt.tz_convert("America/New_York")
        )
        df_gld.set_index("date", inplace=True)
        df_gld.index = market_open_index
        df_gld.index.name = "date"

        # cut df to 2019-01-01 to 2019-03-31
        df_gld = df_gld.loc["2019-01-01":"2019-03-31"]  # type: ignore
        self.prices_gld = df_gld[["open", "high", "low", "close", "volume"]]

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

        # Create strategies for both AAPL and GLD
        self.strategy_aapl = LongHold(
            stock_symbol="AAPL",
            prices=self.prices_aapl.copy(),
        )
        self.strategy_gld = LongHold(
            stock_symbol="GLD",
            prices=self.prices_gld.copy(),
        )

    def test_allocation_runs_full_history(self) -> None:
        # Create allocation with 70% AAPL and 30% GLD
        allocation = FixRatioFrequencyBasedAllocation(
            config=self.config,
            strategies=[self.strategy_aapl, self.strategy_gld],
            allocation_ratio_list=[0.7, 0.3],
            rebalance_frequency=RebalanceFrequency.mid_of_month,
            market_name="NYSE",
        )

        allocation.walk_forward()
        strategy_quantity_map = allocation.strategy_ratio_map

        # Verify allocation ratios for each strategy at each rebalance date
        aapl_ratios = {}
        gld_ratios = {}
        rebalance_dates_set = set()

        for (step, strategy_name), allocation_percentage in strategy_quantity_map.items():
            rebalance_dates_set.add(step)
            if strategy_name == "LongHold - AAPL":
                aapl_ratios[step] = allocation_percentage
                self.assertEqual(allocation_percentage, 0.7)
            elif strategy_name == "LongHold - GLD":
                gld_ratios[step] = allocation_percentage
                self.assertEqual(allocation_percentage, 0.3)
            else:
                self.fail(f"Unexpected strategy name: {strategy_name}")

        # Verify both strategies have ratios for all rebalance dates
        rebalance_dates = sorted(rebalance_dates_set)
        for step in rebalance_dates:
            self.assertIn(step, aapl_ratios, f"AAPL ratio missing for {step}")
            self.assertIn(step, gld_ratios, f"GLD ratio missing for {step}")

        # Verify rebalance dates match expected mid of month dates
        self.assertListEqual(
            rebalance_dates,
            [
                pd.Timestamp("2019-01-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-02-15 09:30:00-05:00", tz="America/New_York"),
                pd.Timestamp("2019-03-15 09:30:00-04:00", tz="America/New_York"),
            ]
        )

        allocation.evaluate()
        self.assertFalse(allocation.portfolio_df.empty)

        # Verify portfolio has data for both strategies
        strategy_names = allocation.portfolio_df.index.get_level_values(1).unique()
        self.assertIn("LongHold - AAPL", strategy_names)
        self.assertIn("LongHold - GLD", strategy_names)

        print("Portfolio DataFrame top 16 and bottom 16 rows:")
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value']].head(16))
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value']].tail(16))

        print("Portfolio Result Metrics:")
        metrics = allocation.get_performance_metrics(plot=True)
        print(metrics)






