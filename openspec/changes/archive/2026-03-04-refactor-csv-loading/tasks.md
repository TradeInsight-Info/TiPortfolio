## 1. Refactor load_csvs function

- [x] 1.1 Remove OHLC transformation logic from load_csvs function
- [x] 1.2 Simplify load_csvs to only return raw DataFrames
- [x] 1.3 Update load_csvs documentation to reflect new behavior

## 2. Update test fixtures

- [x] 2.1 Remove OHLC transformation logic from conftest.py test_prices fixture
- [x] 2.2 Update test_prices to use load_price_df for OHLC format files
- [x] 2.3 Verify test fixtures still provide expected data structure

## 3. Update code usages

- [x] 3.1 Search for all usages of load_csvs in the codebase
- [x] 3.2 Update any code using load_csvs for OHLC files to use load_price_df
- [x] 3.3 Ensure all CSV loading uses appropriate function for the format

## 4. Verification and testing

- [x] 4.1 Run all tests to ensure no regressions
- [x] 4.2 Verify timezone handling works correctly with load_price_df
- [x] 4.3 Test that load_csvs returns raw data without transformation
