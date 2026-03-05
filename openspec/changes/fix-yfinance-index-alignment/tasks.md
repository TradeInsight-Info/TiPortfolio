# Implementation Tasks: Fix YFinance Index Alignment

## 1. Core Fix Implementation

- [x] 1.1 Add explicit DatetimeIndex conversion after YFinance data is fetched and set_index('date') is called
- [x] 1.2 Insert pd.to_datetime() conversion with isinstance() check to handle non-DatetimeIndex cases
- [x] 1.3 Update plot_portfolio_beta() to normalize both asset_curves and benchmark_prices to tz-naive before reindex
- [x] 1.4 Verify fix handles both tz-aware and tz-naive indices from YFinance

## 2. Testing

- [x] 2.1 Run existing test suite to confirm no regressions (135 tests pass)
- [x] 2.2 Create simple integration test: backtest without explicit benchmark_prices, call plot_portfolio_beta()
- [x] 2.3 Verify chart is generated without "Not enough overlapping dates" error
- [x] 2.4 Test with different date ranges and symbol combinations

## 3. Code Quality

- [x] 3.1 Run black formatter on modified code
- [x] 3.2 Run mypy type checker - verify no new errors introduced
- [x] 3.3 Review error messages for clarity and debugging value
- [x] 3.4 Ensure caching mechanism (_cached_benchmark) still works correctly

## 4. Documentation and Cleanup

- [x] 4.1 Update plot_portfolio_beta() docstring with example of YFinance auto-fetch
- [x] 4.2 Add comment explaining DatetimeIndex conversion requirement
- [x] 4.3 Verify no temporary files or .bak files remain
- [x] 4.4 Run full test suite one final time to confirm all 135+ tests pass
