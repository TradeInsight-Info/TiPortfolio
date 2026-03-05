## Why

Currently, plotting functionality requires importing standalone functions from `tiportfolio.report` and explicitly passing `BacktestResult` objects. This scattered approach makes the API less intuitive and forces users to remember which function to call for different visualizations. Moving these capabilities directly onto `BacktestResult` provides a more cohesive and Pythonic interface.

## What Changes

1. Add `plot_portfolio()` method to `BacktestResult` class - moves `plot_portfolio_with_assets_interactive` functionality
2. Add `plot_rolling_book_composition()` method to `BacktestResult` class - visualizes which assets were in long/short books over time
3. Add `plot_portfolio_beta()` method to `BacktestResult` class - shows rolling portfolio beta over time
4. Update `tiportfolio/__init__.py` exports to remove deprecated standalone function imports (or mark as backward compatible)
5. Add type annotations and docstrings to new methods

## Capabilities

### New Capabilities
- `result-plotting`: New methods on BacktestResult for portfolio visualization (plot_portfolio, plot_rolling_book_composition, plot_portfolio_beta)

### Modified Capabilities
- `backtest-engine`: Add new methods to BacktestResult dataclass (delta spec)

## Impact

- **API Change**: Users can now call `result.plot_portfolio()` instead of importing `plot_portfolio_with_assets_interactive(result)`
- **Backwards Compatibility**: Keep old functions in report.py but mark as deprecated/warning
- **Code Location**: New methods added to `src/tiportfolio/backtest.py`
