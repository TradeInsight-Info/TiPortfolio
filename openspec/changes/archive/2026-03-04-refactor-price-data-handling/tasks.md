## 1. Implement Index Normalization Utility

- [x] 1.1 Create normalize_price_index function in calendar.py to ensure DataFrame indices have NYSE timezone and 00:00:00 time
- [x] 1.2 Add unit tests for normalize_price_index with various input scenarios (naive datetime, different timezones, already normalized)

## 2. Update BacktestEngine Price Data Handling

- [x] 2.1 Modify BacktestEngine.__init__ to accept price_dfs as dict of DataFrames instead of dict of Series
- [x] 2.2 Add OHLC column validation in __init__ (check for 'open', 'high', 'low', 'close' columns)
- [x] 2.3 Apply normalize_price_index to each DataFrame in price_dfs during initialization
- [x] 2.4 Update price data access in run method to use df['close'] instead of series values

## 3. Update Test Suite

- [x] 3.1 Update existing BacktestEngine tests to pass DataFrame dictionaries with OHLC data
  - [x] 3.1.1 Update test_simple_rebalance_qqq_bil_gld_rebalance.py to use *_df.csv files instead of series csv files
  - [x] 3.1.2 Find other tests that use series csv format (load_csv with price_column) instead of df csv format
  - [x] 3.1.3 Update all identified (QQQ, BIL, GLD) tests to use df csv format instead of series csv format
  - [x] ~~3.1.4 Update expected CSV files (summary and decisions) to match results from df csv data~~
- [x] 3.2 Update notebook examples (start_of_month_rebalance.ipynb, vix_target_rebalance.ipynb) to create and pass DataFrame dict
- [x] 3.3 Run existing tests to ensure BacktestEngine changes don't break functionality

## 4. Add Data Validation Tests

- [x] 4.1 Create test_data_validation.py in tests/ directory
- [x] 4.2 Implement parametrized pytest fixtures for BIL, QQQ, GLD symbols
- [x] 4.3 Add test functions to compare CSV price column with DataFrame close column values
- [x] 4.4 Run data validation tests to verify they pass with current data

## 5. Make Timezone Configurable

- [ ] 5.1 Add `tz` parameter to `BacktestEngine.run()` method with default 'America/New_York'
- [ ] 5.2 Update `normalize_price_index` to accept `tz` parameter and convert all indices to the specified timezone
- [ ] 5.3 Update tests and notebooks to use the new tz parameter if needed
- [ ] 5.4 Verify that data from different timezones is correctly normalized

## 6. Cleanup and Remove Unused Code

- [ ] 6.1 Locate and remove all usages of prices_dict_from_long_format function
- [ ] 6.2 Delete prices_dict_from_long_format function definition
- [ ] 6.3 Update any imports or references to the removed function
## 6. Update notebooks

- [ ] 6.1 At vix_target_rebalance.ipynb, load vsx_2081_2024_df.csv as vix_df, and use it for Vix Based Backtest engine


## 7. Update tests
- [ ] 7.1 include test case for new normilization utility
- [ ] make sure existing tests get updatee to follow refactoring and pass