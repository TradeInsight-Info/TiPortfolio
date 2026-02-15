import pandas as pd
import numpy as np
from unittest import TestCase
from datetime import datetime
from tiportfolio.portfolio.allocation.vix_targeting import VixTargetingAllocation
from tiportfolio.portfolio.allocation.allocation import (
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
from tiportfolio.portfolio.allocation.frequency_based_allocation import RebalanceFrequency
from tiportfolio.strategy_library.trading.long_hold import LongHold
from tiportfolio.portfolio.types import TradingSignal

class TestVixTargetingAllocation(TestCase):
    def setUp(self) -> None:
        # Create synthetic dates for 10 days
        self.dates = pd.date_range("2025-01-01", periods=10, freq="D")
        
        # Create synthetic VIX data: 10.0, 20.0, 30.0, 40.0, 50.0, ...
        self.vix_values = [10.0, 20.0, 30.0, 40.0, 50.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        self.vix_data = pd.Series(self.vix_values, index=self.dates)
        
        # Create synthetic price data for one asset
        self.prices = pd.DataFrame(
            {
                "open": [100.0] * 10,
                "high": [105.0] * 10,
                "low": [95.0] * 10,
                "close": [102.0] * 10,
                "volume": [1000] * 10,
            },
            index=self.dates,
        )
        self.prices.index.name = "date"
        
        self.config: PortfolioConfig = {
            "commission": 0.0,
            "slippage": 0.0,
            "risk_free_rate": 0.0,
            "initial_capital": 100_000.0,
            "market_name": "NYSE",
        }
        
        self.strategy = LongHold(
            stock_symbol="TEST_STOCK",
            prices=self.prices.copy(),
        )

    def test_initialization(self) -> None:
        target_vol = 15.0
        max_leverage = 1.2
        alloc = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy],
            vix_data=self.vix_data,
            target_vol=target_vol,
            max_leverage=max_leverage,
        )
        self.assertEqual(alloc.target_vol, target_vol)
        self.assertEqual(alloc.max_leverage, max_leverage)
        pd.testing.assert_series_equal(alloc.vix_data, self.vix_data)

    def test_get_target_ratio_single_strategy(self) -> None:
        # target_vol=20.0, max_leverage=1.0
        alloc = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy],
            vix_data=self.vix_data,
            target_vol=20.0,
            max_leverage=1.0,
        )
        
        # Step 0: VIX=10.0 -> weight = 20/10 = 2.0 -> capped to 1.0
        ratio = alloc.get_target_ratio(self.dates[0], self.strategy.name)
        self.assertEqual(ratio, 1.0)
        
        # Step 1: VIX=20.0 -> weight = 20/20 = 1.0
        ratio = alloc.get_target_ratio(self.dates[1], self.strategy.name)
        self.assertEqual(ratio, 1.0)
        
        # Step 3: VIX=40.0 -> weight = 20/40 = 0.5
        ratio = alloc.get_target_ratio(self.dates[3], self.strategy.name)
        self.assertEqual(ratio, 0.5)

    def test_get_target_ratio_multiple_strategies(self) -> None:
        strategy2 = LongHold(
            stock_symbol="TEST_STOCK_2",
            prices=self.prices.copy(),
        )
        
        # target_vol=20.0, max_leverage=1.0
        alloc = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy, strategy2],
            vix_data=self.vix_data,
            target_vol=20.0,
            max_leverage=1.0,
        )
        
        # Step 3: VIX=40.0 -> total weight = 0.5 -> each gets 0.25
        ratio1 = alloc.get_target_ratio(self.dates[3], self.strategy.name)
        ratio2 = alloc.get_target_ratio(self.dates[3], strategy2.name)
        self.assertEqual(ratio1, 0.25)
        self.assertEqual(ratio2, 0.25)

    def test_get_target_ratio_cash(self) -> None:
        alloc = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy],
            vix_data=self.vix_data,
            target_vol=20.0,
            max_leverage=1.0,
        )
        
        # Step 3: VIX=40.0 -> risky weight = 0.5 -> cash weight = 0.5
        ratio = alloc.get_target_ratio(self.dates[3], CASH_STRATEGY_NAME)
        self.assertEqual(ratio, 0.5)
        
        # Step 0: VIX=10.0 -> risky weight = 1.0 -> cash weight = 0.0
        ratio = alloc.get_target_ratio(self.dates[0], CASH_STRATEGY_NAME)
        self.assertEqual(ratio, 0.0)

    def test_get_target_ratio_missing_vix(self) -> None:
        # VIX data only for dates[1:]
        incomplete_vix = self.vix_data[1:]
        alloc = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy],
            vix_data=incomplete_vix,
            target_vol=20.0,
        )
        
        # dates[0] is before any VIX data -> asof should return NaN -> weight 0.0
        ratio = alloc.get_target_ratio(self.dates[0], self.strategy.name)
        self.assertEqual(ratio, 0.0)
        
        # Add a NaN in the middle
        vix_with_nan = self.vix_data.copy()
        vix_with_nan.iloc[5] = np.nan
        alloc_nan = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy],
            vix_data=vix_with_nan,
            target_vol=20.0,
        )
        
        # dates[5] is NaN -> asof(dates[5]) will return the value at dates[4] (50.0)
        # because asof skips NaNs by default in some versions or returns last valid.
        # Actually pandas asof behavior: "For a sorted index, returns the last row of the DataFrame 
        # whose index is on or before the given value." 
        # If the value at that index is NaN, it returns NaN.
        # Let's verify our implementation uses asof correctly.
        # Our implementation: vix_value = self.vix_data.asof(current_step)
        
        ratio = alloc_nan.get_target_ratio(self.dates[5], self.strategy.name)
        # vix_data[5] is NaN, so asof(dates[5]) returns vix_data[4]=50.0
        self.assertEqual(ratio, 20.0/50.0)

    def test_walk_forward_evaluation(self) -> None:
        alloc = VixTargetingAllocation(
            config=self.config,
            strategies=[self.strategy],
            vix_data=self.vix_data,
            target_vol=20.0,
            max_leverage=1.0,
            rebalance_frequency=RebalanceFrequency.daily
        )
        
        alloc.walk_forward()
        
        # Check strategy_ratio_map
        # Rebalance daily at 09:30. But our synthetic dates are just dates.
        # FrequencyBasedAllocation uses the hour/minute provided.
        # setup sets dates as 2025-01-01 00:00:00
        # Rebalance frequency default is daily at 09:30.
        # So we need to align our price/vix dates or adjust rebalance hour.
        
        # Let's adjust rebalance hour to 0 for the test
        alloc.rebalance_hour = 0
        alloc.rebalance_minute = 0
        
        # Re-run walk_forward
        alloc.strategy_ratio_map = {}
        alloc._step_weights = {}
        alloc.walk_forward()
        
        # Verify ratio at step 3 (VIX=40.0)
        self.assertEqual(alloc.strategy_ratio_map[(self.dates[3], self.strategy.name)], 0.5)
        
        alloc.evaluate()
        self.assertFalse(alloc.portfolio_df.empty)
        
        # On first step (VIX=10.0), target ratio=1.0
        # Value should be initial_capital * 1.0 (minus fees, but commission is 0)
        val = alloc.portfolio_df.at[(self.dates[0], self.strategy.name), "value"]
        self.assertEqual(val, self.config["initial_capital"])
