import pandas as pd
import numpy as np
from unittest import TestCase
from tiportfolio.portfolio.allocation.vix_targeting import VixTargetingAllocation
from tiportfolio.portfolio.allocation.allocation import (
    CASH_STRATEGY_NAME,
    PortfolioConfig,
)
from tiportfolio.strategy_library.trading.long_hold import LongHold

class TestVixTargetingAllocation(TestCase):
    def setUp(self) -> None:
        # 10 days of data
        self.dates = pd.date_range("2025-01-01", periods=10, freq="D")
        
        # VIX: 20 (start), then 20, 20, 40 (high), 20, 20, 10 (low), 20, 20, 20
        self.vix_values = [20.0, 20.0, 20.0, 40.0, 20.0, 20.0, 10.0, 20.0, 20.0, 20.0]
        self.vix_data = pd.Series(self.vix_values, index=self.dates)
        
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
        
        self.strategy_voo = LongHold("VOO", self.prices.copy())
        self.strategy_bil = LongHold("BIL", self.prices.copy())

    def test_threshold_rebalance_trigger(self) -> None:
        # Range 15 to 30
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            self.vix_data, [0.5, 0.1], target_vol=15.0, target_range=(15.0, 30.0)
        )
        
        # Step 0: First step -> Rebalance
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[0]))
        
        # Step 1: VIX=20 (in range) -> No rebalance
        self.assertFalse(alloc.is_time_to_rebalance(self.dates[1]))
        
        # Step 3: VIX=40 (out of high side) -> Rebalance
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[3]))
        
        # Step 4: VIX=20 (back in range) -> No rebalance
        self.assertFalse(alloc.is_time_to_rebalance(self.dates[4]))
        
        # Step 6: VIX=10 (out of low side) -> Rebalance
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[6]))

    def test_weight_calculation_erc_vol_targeting(self) -> None:
        # target_vol=20, flags=[0.5, 0.1], VIX=20
        # W_voo = 20 / (2 * 20 * 0.5) = 20 / 20 = 1.0
        # W_bil = 20 / (2 * 20 * 0.1) = 20 / 4 = 5.0
        # Total = 6.0 -> capped to 1.0
        # Scaling = 1/6
        # W_voo = 1/6, W_bil = 5/6
        
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            self.vix_data, [0.5, 0.1], target_vol=20.0, max_leverage=1.0
        )
        
        w_voo = alloc.get_target_ratio(self.dates[0], self.strategy_voo.name)
        w_bil = alloc.get_target_ratio(self.dates[0], self.strategy_bil.name)
        w_cash = alloc.get_target_ratio(self.dates[0], CASH_STRATEGY_NAME)
        
        self.assertAlmostEqual(w_voo, 1/6)
        self.assertAlmostEqual(w_bil, 5/6)
        self.assertAlmostEqual(w_cash, 0.0)
        
        # VIX=40 (Step 3)
        # W_voo = 20 / (2 * 40 * 0.5) = 20 / 40 = 0.5
        # W_bil = 20 / (2 * 40 * 0.1) = 20 / 8 = 2.5
        # Total = 3.0 -> capped to 1.0
        # Scaling = 1/3
        # W_voo = 0.5 * 1/3 = 1/6
        # W_bil = 2.5 * 1/3 = 5/6
        # Wait, if we always cap when sum > 1, the ratio stays 1:5.
        
        w_voo_3 = alloc.get_target_ratio(self.dates[3], self.strategy_voo.name)
        self.assertAlmostEqual(w_voo_3, 1/6)

    def test_weight_calculation_with_cash(self) -> None:
        # Set target_vol low so we have cash
        # target_vol=2, flags=[0.5, 0.1], VIX=20
        # W_voo = 2 / (2 * 20 * 0.5) = 2 / 20 = 0.1
        # W_bil = 2 / (2 * 20 * 0.1) = 2 / 4 = 0.5
        # Total = 0.6. Cash = 0.4.
        
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            self.vix_data, [0.5, 0.1], target_vol=2.0
        )
        
        self.assertAlmostEqual(alloc.get_target_ratio(self.dates[0], self.strategy_voo.name), 0.1)
        self.assertAlmostEqual(alloc.get_target_ratio(self.dates[0], self.strategy_bil.name), 0.5)
        self.assertAlmostEqual(alloc.get_target_ratio(self.dates[0], CASH_STRATEGY_NAME), 0.4)

    def test_walk_forward_integration(self) -> None:
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo],
            self.vix_data, [0.5], target_vol=5.0, target_range=(15, 30)
        )
        
        alloc.walk_forward()
        # Step 0: VIX=20 -> W = 5 / (1 * 20 * 0.5) = 0.5
        # Step 3: VIX=40 -> W = 5 / (1 * 40 * 0.5) = 0.25
        # Step 6: VIX=10 -> W = 5 / (1 * 10 * 0.5) = 1.0
        
        self.assertEqual(alloc.strategy_ratio_map[(self.dates[0], self.strategy_voo.name)], 0.5)
        self.assertEqual(alloc.strategy_ratio_map[(self.dates[3], self.strategy_voo.name)], 0.25)
        self.assertEqual(alloc.strategy_ratio_map[(self.dates[6], self.strategy_voo.name)], 1.0)
        
        # Step 1 should have NO entry in strategy_ratio_map because no rebalance
        self.assertNotIn((self.dates[1], self.strategy_voo.name), alloc.strategy_ratio_map)
