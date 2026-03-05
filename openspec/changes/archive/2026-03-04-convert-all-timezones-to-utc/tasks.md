## 1. Update Core Normalization Function

- [x] 1.1 Change `normalize_price_index` default timezone parameter from 'America/New_York' to 'UTC'
- [x] 1.2 Update `normalize_price_index` logic to properly handle UTC conversions for mixed and uniform timezones

## 2. Update Engine Classes

- [x] 2.1 Update `BacktestEngine.run` method to pass 'UTC' as timezone parameter
- [x] 2.2 Update `ScheduleBasedEngine.run` and `VolatilityBasedEngine.run` to use UTC timezone
- [x] 2.3 Update any normalization calls in engine methods to use UTC

## 3. Update Data Loading Functions

- [x] 3.1 Update `load_price_df` to parse dates as UTC instead of localizing later
- [x] 3.2 Verify other data loading functions handle UTC correctly

## 4. Update Tests

- [x] 4.1 Update test assertions in `test_calendar.py` to expect UTC conversions
- [x] 4.2 Update test data loading in `test_simple_rebalance_qqq_bil_gld_rebalance.py` to use UTC parsing
- [x] 4.3 Update expected CSV results to reflect UTC-based calculations

## 5. Validation and Documentation

- [x] 5.1 Run full test suite to ensure all changes work correctly
- [x] 5.2 Verify that DST-related edge cases are resolved
- [x] 5.3 Update any documentation mentioning timezone handling
- [x] 5.4 Test rollback procedure (revert timezone to 'America/New_York')
