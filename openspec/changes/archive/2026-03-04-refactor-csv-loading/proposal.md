## Why

The current CSV loading logic has mixed responsibilities - `load_csvs` contains data transformation logic while `load_price_df` handles OHLC format loading. This creates confusion and inconsistent data loading patterns across the codebase.

## What Changes

- **BREAKING**: Remove data transformation logic from `load_csvs` - it will only load raw CSV files as DataFrames
- Refactor `load_csvs` to use `load_price_df` for OHLC format files
- Ensure all CSV loading functions have single, clear responsibilities
- Update test fixtures and usages to handle the simplified CSV loading

## Capabilities

### New Capabilities
- `csv-loading`: Standardized CSV loading with clear separation between raw loading and data transformation

### Modified Capabilities
- `data-loading`: Simplified CSV loading interface that delegates OHLC loading to `load_price_df`

## Impact

- Affected code: `src/tiportfolio/data.py` (load_csvs function)
- Test fixtures: `tests/conftest.py` (test data setup)
- Any code using `load_csvs` for OHLC format files will need to use `load_price_df` directly
