## Why

The current BacktestEngine receives price data as a dictionary of Series containing only close prices, limiting flexibility and making it harder to work with larger datasets. To improve usability and data handling, we need to refactor it to use real DataFrames with full OHLC price data and normalized datetime indices with configurable timezone information.

## What Changes

- **BREAKING**: Update BacktestEngine to accept `price_dfs` as a dictionary of DataFrames (OHLC prices) instead of dictionary of Series (close prices only).
- Implement an index normalizer utility that ensures DataFrame indices have proper datetime timezone information, converting all indices to the specified timezone (default NYSE TZ, 00:00:00 time) for data from various sources like yfinance.
- Add `tz` parameter to `BacktestEngine.run()` method to specify the target timezone for normalization, defaulting to 'America/New_York'.
- Remove usage of `prices_dict_from_long_format` function as it's no longer needed.
- Add comprehensive tests to validate that CSV data files (e.g., `bil_2018_2024.csv` price column matches `bil_2018_2024_df.csv` close column) are consistent for all BIL, QQQ, GLD datasets.

## Capabilities

### New Capabilities
- `data-validation`: Automated tests to ensure consistency between price data CSV files and their DataFrame equivalents.

### Modified Capabilities
- `backtest-engine`: Update price data handling to use DataFrame dictionaries with OHLC prices and normalized timezone-aware indices, with configurable timezone support.

## Impact

- BacktestEngine initialization and run methods will change to handle DataFrame inputs and optional timezone parameter.
- New utility function for index normalization with timezone conversion.
- Test suite will include data validation tests for CSV files in `tests/data`.
- No external dependencies affected, but pandas DataFrame handling will be more robust and flexible for different data sources.
