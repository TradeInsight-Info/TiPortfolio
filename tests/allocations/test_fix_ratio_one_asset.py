from pathlib import Path
from unittest import TestCase

import pandas as pd

from tiportfolio.portfolio.allocation.allocation import (
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
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
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value']].head(20))
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value']].tail(20))

        # Verify that on 2019-01-15, AAPL value is 99990
        trade_date = pd.Timestamp(
            "2019-01-15 09:30:00-05:00", tz="America/New_York"
        )
        aapl_value = float(  # type: ignore
            allocation.portfolio_df.at[
                (trade_date, "LongHold - AAPL"), 'value'
            ]
        )
        self.assertEqual(aapl_value, 99990)

        metrics = allocation.get_performance_metrics(True)
        print(metrics)
        # Verify metrics match expected values
        expected_metrics = {'final_value': 124609.68672712284, 'total_return': 0.2460968672712284,
                            'max_drawdown': -0.0427221983683983, 'sharpe_ratio': np.float64(6.45431584690706),
                            'annualized_return': 1.5195186509091725, 'mar_ratio': 5.7603980288913865}

        self.assertAlmostEqual(
            metrics['final_value'], expected_metrics['final_value'], places=5
        )
        self.assertAlmostEqual(
            metrics['total_return'], expected_metrics['total_return'], places=5
        )
        self.assertAlmostEqual(
            metrics['max_drawdown'], expected_metrics['max_drawdown'], places=5
        )
        self.assertAlmostEqual(
            float(metrics['sharpe_ratio']),  # type: ignore
            expected_metrics['sharpe_ratio'],
            places=5
        )
        self.assertAlmostEqual(
            metrics['annualized_return'],
            expected_metrics['annualized_return'],
            places=5
        )
        self.assertAlmostEqual(
            metrics['mar_ratio'], expected_metrics['mar_ratio'], places=5
        )
from pathlib import Path
from unittest import TestCase

import pandas as pd

from tiportfolio.portfolio.allocation.allocation import (
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
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
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value']].head(20))
        print(allocation.portfolio_df[['signal', 'close', 'quantity', 'value']].tail(20))

        # Verify that on 2019-01-15, AAPL value is 99990
        trade_date = pd.Timestamp(
            "2019-01-15 09:30:00-05:00", tz="America/New_York"
        )
        aapl_value = float(  # type: ignore
            allocation.portfolio_df.at[
                (trade_date, "LongHold - AAPL"), 'value'
            ]
        )
        self.assertEqual(aapl_value, 99990)

        metrics = allocation.get_performance_metrics(True)
        # Verify metrics match expected values
        expected_metrics = {'final_value': 124609.68672712284, 'total_return': 0.2460968672712284,
                            'max_drawdown': -0.0427221983683983, 'sharpe_ratio': 6.45431584690706,
                            'annualized_return': 1.5195186509091725, 'mar_ratio': 5.7603980288913865}

        self.assertAlmostEqual(
            metrics['final_value'], expected_metrics['final_value'], places=5
        )
        self.assertAlmostEqual(
            metrics['total_return'], expected_metrics['total_return'], places=5
        )
        self.assertAlmostEqual(
            metrics['max_drawdown'], expected_metrics['max_drawdown'], places=5
        )
        self.assertAlmostEqual(
            float(metrics['sharpe_ratio']),  # type: ignore
            expected_metrics['sharpe_ratio'],
            places=5
        )
        self.assertAlmostEqual(
            metrics['annualized_return'],
            expected_metrics['annualized_return'],
            places=5
        )
        self.assertAlmostEqual(
            metrics['mar_ratio'], expected_metrics['mar_ratio'], places=5
        )
