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
        # Range 15 to 30 (target_vol 15 + vix_boundaries 0 and 15)
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            self.vix_data, 
            base_weights={self.strategy_voo.name: 0.9, self.strategy_bil.name: 0.1}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=15.0, 
            vix_boundaries=(0.0, 15.0)
        )
        
        # Step 0: First step -> Rebalance
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[0]))
        
        # Step 1: VIX=20 (in range) -> No rebalance
        self.assertFalse(alloc.is_time_to_rebalance(self.dates[1]))
        
        # Step 3: VIX=40 (out of high side) -> Rebalance
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[3]))
        
        # Step 4: VIX=20 (back in range) -> Rebalance (edge trigger from high to normal)
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[4]))
        
        # Step 5: VIX=20 (still in range) -> No rebalance
        self.assertFalse(alloc.is_time_to_rebalance(self.dates[5]))
        
        # Step 6: VIX=10 (out of low side) -> Rebalance
        self.assertTrue(alloc.is_time_to_rebalance(self.dates[6]))

    def test_threshold_rebalance_trigger_negative_boundary(self) -> None:
        # target_vol=15.0, boundaries=(-1.0, 5.0) -> low=14.0, high=20.0
        dates = pd.date_range("2025-01-01", periods=6, freq="D")
        
        vix_data = pd.Series([15.0, 19.0, 21.0, 14.5, 13.0, 13.0], index=dates)
        
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            vix_data, 
            base_weights={self.strategy_voo.name: 0.9, self.strategy_bil.name: 0.1}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=15.0, 
            vix_boundaries=(-1.0, 5.0)
        )
        
        self.assertTrue(alloc.is_time_to_rebalance(dates[0]))
        self.assertFalse(alloc.is_time_to_rebalance(dates[1]))
        self.assertTrue(alloc.is_time_to_rebalance(dates[2]))
        self.assertTrue(alloc.is_time_to_rebalance(dates[3]))
        self.assertTrue(alloc.is_time_to_rebalance(dates[4]))
        self.assertFalse(alloc.is_time_to_rebalance(dates[5]))

    def test_weight_calculation_base_weights(self) -> None:
        # Normal case
        # target_vol=15, VIX=20
        # M = 15/20 = 0.75
        # w_voo = 0.9 * 0.75 = 0.675
        # w_bil = 1.0 - 0.675 = 0.325
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            self.vix_data, 
            base_weights={self.strategy_voo.name: 0.9, self.strategy_bil.name: 0.1}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=15.0, 
            max_leverage=1.0
        )
        
        w_voo = alloc.get_target_ratio(self.dates[0], self.strategy_voo.name)
        w_bil = alloc.get_target_ratio(self.dates[0], self.strategy_bil.name)
        w_cash = alloc.get_target_ratio(self.dates[0], CASH_STRATEGY_NAME)
        
        self.assertAlmostEqual(w_voo, 0.675)
        self.assertAlmostEqual(w_bil, 0.325)
        self.assertAlmostEqual(w_cash, 0.0)
        
        # Capped case
        # target_vol=30, VIX=20
        # M = 30/20 = 1.5
        # w_voo = 0.9 * 1.5 = 1.35 -> Capped to 1.0
        # w_bil = 1.0 - 1.0 = 0.0
        alloc_capped = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            self.vix_data, 
            base_weights={self.strategy_voo.name: 0.9, self.strategy_bil.name: 0.1}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=30.0, 
            max_leverage=1.0
        )
        
        w_voo_capped = alloc_capped.get_target_ratio(self.dates[0], self.strategy_voo.name)
        w_bil_capped = alloc_capped.get_target_ratio(self.dates[0], self.strategy_bil.name)
        
        self.assertAlmostEqual(w_voo_capped, 1.0)
        self.assertAlmostEqual(w_bil_capped, 0.0)

    def test_weight_calculation_with_cash(self) -> None:
        # target_vol=10, VIX=20
        # M = 10/20 = 0.5
        # No safe assets provided (only VOO in strategies)
        # w_voo = 0.9 * 0.5 = 0.45
        # Cash = 1.0 - 0.45 = 0.55
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo],
            self.vix_data, 
            base_weights={self.strategy_voo.name: 0.9}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=10.0
        )
        
        self.assertAlmostEqual(alloc.get_target_ratio(self.dates[0], self.strategy_voo.name), 0.45)
        self.assertAlmostEqual(alloc.get_target_ratio(self.dates[0], CASH_STRATEGY_NAME), 0.55)

    def test_walk_forward_integration(self) -> None:
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo],
            self.vix_data, 
            base_weights={self.strategy_voo.name: 0.9}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=15.0, 
            vix_boundaries=(0.0, 15.0)
        )
        
        alloc.walk_forward()
        # Step 0: VIX=20 -> M = 15/20 = 0.75. W = 0.9 * 0.75 = 0.675
        # Step 3: VIX=40 -> M = 15/40 = 0.375. W = 0.9 * 0.375 = 0.3375
        # Step 4: VIX=20 -> W = 0.675
        # Step 6: VIX=10 -> M = 15/10 = 1.5. W = 0.9 * 1.5 = 1.35 -> Capped to 1.0
        
        self.assertAlmostEqual(alloc.strategy_ratio_map[(self.dates[0], self.strategy_voo.name)], 0.675)
        self.assertAlmostEqual(alloc.strategy_ratio_map[(self.dates[3], self.strategy_voo.name)], 0.3375)
        self.assertAlmostEqual(alloc.strategy_ratio_map[(self.dates[4], self.strategy_voo.name)], 0.675)
        self.assertAlmostEqual(alloc.strategy_ratio_map[(self.dates[6], self.strategy_voo.name)], 1.0)
        
        # Step 1 should have NO entry in strategy_ratio_map because no rebalance
        self.assertNotIn((self.dates[1], self.strategy_voo.name), alloc.strategy_ratio_map)

    def test_get_target_ratio_caching_on_non_rebalance_day(self) -> None:
        dates = pd.date_range("2025-01-01", periods=3, freq="D")
        # Step 0: 20 (rebalance, normal regime)
        # Step 1: 25 (no rebalance, still normal)
        vix_data = pd.Series([20.0, 25.0, 25.0], index=dates)
        
        alloc = VixTargetingAllocation(
            self.config, [self.strategy_voo, self.strategy_bil],
            vix_data, 
            base_weights={self.strategy_voo.name: 0.9, self.strategy_bil.name: 0.1}, 
            risky_assets=[self.strategy_voo.name], 
            target_vol=15.0, 
            vix_boundaries=(0.0, 15.0)
        )
        
        w_voo_0 = alloc.get_target_ratio(dates[0], self.strategy_voo.name)
        
        # At step 1, VIX is 25. If it recalculated, w_voo would be lower.
        # But since it's not a rebalance day, it should return cached weights from step 0 (VIX=20).
        w_voo_1 = alloc.get_target_ratio(dates[1], self.strategy_voo.name)
        self.assertEqual(w_voo_0, w_voo_1)
