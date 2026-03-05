## Why

When calling `BacktestResult.plot_portfolio_beta()` without explicit benchmark prices, the method fetches benchmark data from YFinance. However, YFinance returns data with a RangeIndex (numeric 0-N) instead of a DatetimeIndex, causing the index alignment logic to fail. The reindex operation then produces all NaN values, resulting in the error "Not enough overlapping dates. Need at least 61, got 0".

This blocks notebook users from using the beta chart functionality when they don't have pre-fetched benchmark data.

## What Changes

Fix the YFinance data handling in `BacktestResult.plot_portfolio_beta()` to properly convert the returned data's index to a DatetimeIndex before performing index alignment operations.

- Ensure `benchmark_data` returned from YFinance is converted from RangeIndex to DatetimeIndex
- Add explicit DatetimeIndex conversion after setting the 'date' column as index
- Verify the fix handles edge cases (missing 'date' column, timezone mismatches)

## Capabilities

### New Capabilities
- `yfinance-index-conversion`: Properly convert YFinance returned data with RangeIndex to DatetimeIndex for alignment

### Modified Capabilities
- `plot-portfolio-beta-functionality`: Fix YFinance integration to work correctly when benchmark_prices not provided

## Impact

- **Files modified**: `src/tiportfolio/backtest.py` (plot_portfolio_beta method)
- **APIs affected**: None (internal fix)
- **Tests**: Existing unit tests should pass with fix; integration scenarios now work
- **Users**: Notebooks using `result.plot_portfolio_beta()` without explicit benchmark data can now work
