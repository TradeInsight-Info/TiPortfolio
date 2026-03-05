# Implementation Tasks: Fix Beta Chart Plotting

## 1. Audit and Planning

- [ ] 1.1 Check which `plot_equity_curve()` and `plot_portfolio_with_assets()` calls exist outside of tests (grep codebase and notebooks)
- [ ] 1.2 Document findings: are deprecated functions safe to remove or do they need deprecation warnings?
- [ ] 1.3 Verify current test suite status (run uv run pytest to confirm 126 tests pass)

## 2. Fix plot_portfolio_beta() - Timezone Handling

- [ ] 2.1 Update BacktestResult.plot_portfolio_beta() method signature and docstring
- [ ] 2.2 Implement timezone normalization: convert asset_curves and benchmark_prices indices to tz-naive
- [ ] 2.3 Add fallback to tz-aware UTC if conversion fails
- [ ] 2.4 Write unit tests for timezone handling (tz-naive, tz-aware, mixed)

## 3. Fix plot_portfolio_beta() - Benchmark Data Fetching

- [ ] 3.1 Implement benchmark data fetching from YFinance if benchmark_prices not provided
- [ ] 3.2 Add caching mechanism (_cached_benchmark) to avoid repeated fetches
- [ ] 3.3 Handle YFinance errors gracefully with informative error messages
- [ ] 3.4 Write unit tests for benchmark fetching (provided data, YFinance fallback, missing symbol)

## 4. Fix plot_portfolio_beta() - Rolling Beta Calculation

- [ ] 4.1 Fix index reindexing and alignment logic to find common dates
- [ ] 4.2 Implement overlap validation: raise ValueError if fewer than lookback_days + 1 common dates
- [ ] 4.3 Implement rolling beta calculation using OLS covariance/variance
- [ ] 4.4 Fix NaN handling and edge cases (zero variance, insufficient data)
- [ ] 4.5 Write unit tests for rolling beta calculation (2-asset, multi-asset, insufficient data)

## 5. Fix plot_portfolio_beta() - Chart Formatting

- [ ] 5.1 Add reference lines to Plotly figure (β=1.0 and β=0.0 with labels)
- [ ] 5.2 Format title to show lookback_days
- [ ] 5.3 Configure hover template with date and beta (4 decimals)
- [ ] 5.4 Write unit tests for chart appearance and formatting

## 6. Fix plot_rolling_book_composition()

- [ ] 6.1 Fix asset extraction from asset_curves to identify non-zero positions
- [ ] 6.2 Implement date handling: use rebalance_dates if available, fall back to asset_curves index
- [ ] 6.3 Build heatmap matrix with proper row (assets) and column (dates) ordering
- [ ] 6.4 Implement error handling: raise KeyError for missing column, ValueError for no assets
- [ ] 6.5 Format Plotly heatmap with proper titles, axis labels, and colorscale
- [ ] 6.6 Write unit tests for book composition chart

## 7. Report.py Cleanup

- [ ] 7.1 If deprecated functions are safe to remove: delete `plot_equity_curve()` and `plot_portfolio_with_assets()` from report.py
- [ ] 7.2 If functions need deprecation: add warnings with migration instructions instead
- [ ] 7.3 Verify `compare_strategies()` and `plot_strategy_comparison_interactive()` are unchanged
- [ ] 7.4 Run tests to confirm no regressions in report.py functions

## 8. Update Notebooks

- [ ] 8.1 Fix `start_of_month_rebalance.ipynb`: replace broken beta chart call with corrected method
- [ ] 8.2 Fix `beta_neutral_dynamic.ipynb`: verify beta chart works correctly
- [ ] 8.3 Fix `dollar_neutral_txn_kvue.ipynb`: verify charts render without errors
- [ ] 8.4 Fix `vix_target_rebalance.ipynb`: verify charts render without errors
- [ ] 8.5 Fix `volatility_targeting_qqq_bil_gld.ipynb`: verify charts render without errors
- [ ] 8.6 Test all 5 notebooks end-to-end in Jupyter to confirm no "Not enough overlapping dates" errors

## 9. Testing and Verification

- [ ] 9.1 Run full test suite: uv run pytest (confirm 126+ tests pass)
- [ ] 9.2 Run type checking: uv run mypy src/tiportfolio/backtest.py for new/changed methods
- [ ] 9.3 Create integration test: backtest with all 5 allocation strategies and verify all charts work
- [ ] 9.4 Test in Jupyter notebook: create simple test notebook calling all three chart methods
- [ ] 9.5 Test edge cases: empty rebalance_decisions, single asset, highly correlated assets

## 10. Documentation and Cleanup

- [ ] 10.1 Update docstrings for fixed methods with examples
- [ ] 10.2 Remove or update any outdated comments in backtest.py plotting section
- [ ] 10.3 Verify no temporary files or backups (.bak) are committed
- [ ] 10.4 Run code formatter: uv run black src/tiportfolio/backtest.py
