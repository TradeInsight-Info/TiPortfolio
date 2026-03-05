# Proposal: Fix Beta Chart Plotting and Optimize Report Logic

## Why

The recent update to add `plot_portfolio_beta()` and `plot_rolling_book_composition()` methods to `BacktestResult` introduced data alignment issues and empty chart errors. Notebooks fail with "Not enough overlapping dates" errors or display blank charts. Additionally, report.py contains deprecated plotting functions that should be removed to reduce maintenance burden and clarify the public API.

## What Changes

- **Fix `plot_portfolio_beta()`**: Correct benchmark data fetching, alignment, and rolling beta calculation to handle timezone-naive/aware indices correctly
- **Fix `plot_rolling_book_composition()`**: Ensure proper index handling and book value extraction
- **Update all 5 notebooks**: Replace broken beta chart calls with corrected implementation
- **Audit and remove deprecated functions** from report.py: Remove `plot_equity_curve()` and `plot_portfolio_with_assets()` if unused outside tests
- **Consolidate chart logic**: Ensure BacktestResult methods are the source of truth for charting; report.py functions deprecated or removed as appropriate

## Capabilities

### New Capabilities
- `portfolio-beta-visualization`: Rolling portfolio beta chart with reliable benchmark data fetching, timezone handling, and error recovery
- `book-composition-chart`: Heatmap visualization of long/short book positions over rebalance dates

### Modified Capabilities
- `backtest-result-plotting`: BacktestResult charting methods now handle data alignment robustly and work correctly with notebooks

## Impact

**Affected Code:**
- `src/tiportfolio/backtest.py`: `plot_portfolio_beta()`, `plot_rolling_book_composition()` methods
- `src/tiportfolio/report.py`: Cleanup of deprecated plot functions
- `notebooks/`: All 5 notebooks using beta/book composition charts

**Public API:** Minimal impact if deprecated functions are only internal/test-only; otherwise requires deprecation notice.

**Testing:** Existing 126 tests should continue passing; new unit tests needed for fixed charting methods.
