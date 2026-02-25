import pandas as pd
from tiportfolio.portfolio.allocation.vix_targeting import VixTargetingAllocation
from tiportfolio.strategy_library.trading.long_hold import LongHold

dates = pd.date_range("2025-01-01", periods=3, freq="D")
vix_data = pd.Series([20.0, 25.0, 20.0], index=dates)

prices = pd.DataFrame({"open": [100]*3, "high": [100]*3, "low": [100]*3, "close": [100.0, 100.0, 100.0], "volume": [100]*3}, index=dates)
prices.index.name = "date"
config = {"commission": 0.0, "slippage": 0.0, "risk_free_rate": 0.0, "initial_capital": 100000.0, "market_name": "NYSE"}

strat = LongHold("VOO", prices)
alloc = VixTargetingAllocation(config, [strat], vix_data, [0.5], target_vol=15.0, target_range=(15.0, 30.0), max_leverage=10.0)

print("Day 0 time to rebalance:", alloc.is_time_to_rebalance(dates[0]))
print("Day 0 ratio:", alloc.get_target_ratio(dates[0], strat.name))

# Day 1 is not a rebalance day, but get_target_ratio gets called
print("Day 1 time to rebalance:", alloc.is_time_to_rebalance(dates[1])) # Should be False
print("Day 1 ratio with VIX=25:", alloc.get_target_ratio(dates[1], strat.name))
print("Day 0 ratio again:", alloc.get_target_ratio(dates[0], strat.name))
