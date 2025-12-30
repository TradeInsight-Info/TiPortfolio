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
        # Verify that on 2019-01-15, portfolio values match expected
        trade_date = pd.Timestamp(
            "2019-01-15 09:30:00-05:00", tz="America/New_York"
        )

        # Verify AAPL values
        aapl_signal = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - AAPL"), 'signal']
        )
        aapl_close = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - AAPL"), 'close']
        )
        aapl_quantity = float(  # type: ignore
            allocation.portfolio_df.at[
                (trade_date, "LongHold - AAPL"), 'quantity'
            ]
        )
        aapl_value = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - AAPL"), 'value']
        )
        self.assertEqual(aapl_signal, 1.0)
        self.assertEqual(aapl_close, 36.39)
        self.assertAlmostEqual(aapl_quantity, 1923.413026, places=5)
        self.assertEqual(aapl_value, 69993.0)

        # Verify GLD values
        gld_signal = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - GLD"), 'signal']
        )
        gld_close = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - GLD"), 'close']
        )
        gld_quantity = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - GLD"), 'quantity']
        )
        gld_value = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, "LongHold - GLD"), 'value']
        )
        self.assertEqual(gld_signal, 1.0)
        self.assertEqual(gld_close, 121.88)
        self.assertAlmostEqual(gld_quantity, 246.119134, places=5)
        self.assertEqual(gld_value, 29997.0)

        # Verify cash values
        cash_signal = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, CASH_STRATEGY_NAME), 'signal']
        )
        cash_close = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, CASH_STRATEGY_NAME), 'close']
        )
        cash_quantity = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, CASH_STRATEGY_NAME), 'quantity']
        )
        cash_value = float(  # type: ignore
            allocation.portfolio_df.at[(trade_date, CASH_STRATEGY_NAME), 'value']
        )
        self.assertEqual(cash_signal, 0.0)
        self.assertEqual(cash_close, 1.0)
        self.assertEqual(cash_quantity, 0.0)
        self.assertEqual(cash_value, 0.0)

        metrics = allocation.get_performance_metrics(plot=True)

        # Verify metrics match expected values
        expected_metrics = {
            'final_value': 117255.7761963506,
            'total_return': 0.17255776196350606,
            'max_drawdown': -0.030616668031244743,
            'sharpe_ratio': 5.448534618819549,
            'annualized_return': 0.9514787783567344,
            'mar_ratio': 5.636072540206152
        }
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
