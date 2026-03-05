## 1. Parameter Renaming

- [x] 1.1 Rename `dfs_in_dict` to `prices_df` in ScheduleBasedEngine.run() method
- [x] 1.2 Rename `dfs_in_dict` to `prices_df` in VolatilityBasedEngine.run() method
- [x] 1.3 Update method docstrings to reflect parameter name changes

## 2. VIX Data Handling

- [x] 2.1 Add optional `vix_df` parameter to VolatilityBasedEngine.run() method signature
- [x] 2.2 Modify `_vix_series_from_prices()` to handle separate VIX DataFrame input
- [x] 2.3 Update VIX data extraction logic to prioritize vix_df over prices_df
- [x] 2.4 Add backward compatibility for VIX data in prices_df

## 3. run_backtest Decoupling

- [x] 3.1 Remove engine-specific parameters from VolatilityBasedEngine.run_backtest() call
- [x] 3.2 Handle rebalance_filter, vix_series, context_for_date, schedule_kwargs within engine
- [x] 3.3 Ensure run_backtest calls only use universal parameters
- [x] 3.4 Test that ScheduleBasedEngine still works correctly

## 4. Testing and Validation

- [x] 4.1 Test VolatilityBasedEngine with separate vix_df parameter
- [x] 4.2 Test VolatilityBasedEngine with legacy prices_df approach
- [x] 4.3 Test ScheduleBasedEngine with renamed prices_df parameter
- [x] 4.4 Verify all existing functionality still works
- [x] 4.5 Update any internal tests to use new parameter names

## 5. Fix VIX Data Logic

- [x] 5.1 Fix VIX data extraction to use fetch_volatility_index when vix_df not provided
- [x] 5.2 Remove incorrect requirement that VIX symbol must be in prices dict
- [x] 5.3 Update VIX logic to properly handle three cases: vix_df provided, fetch needed, legacy fallback

## 6. Fix run_backtest Coupling

- [x] 6.1 Remove all engine-specific parameters from run_backtest calls
- [x] 6.2 Handle rebalance_filter logic within VolatilityBasedEngine before calling run_backtest
- [x] 6.3 Handle vix_regime context_for_date logic within VolatilityBasedEngine
- [x] 6.4 Ensure run_backtest only receives universal parameters
- [x] 6.5 Test that run_backtest is truly engine-agnostic
