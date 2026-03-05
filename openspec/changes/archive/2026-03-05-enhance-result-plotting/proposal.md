## Why

The BacktestResult class now has plotting methods (plot_portfolio, plot_rolling_book_composition, plot_portfolio_beta). We need to update plot_portfolio_beta to auto-fetch benchmark data if not provided, clean up unused functions in report.py, and update notebooks to use these new methods.

## What Changes

1. Update plot_portfolio_beta to auto-fetch SPY benchmark if not provided
2. Clean up unused/deprecated functions from report.py
3. Update notebooks to use result.plot_portfolio_beta() with auto-fetch

## Capabilities

### Modified Capabilities
- `backtest-engine`: Update plot_portfolio_beta to auto-fetch benchmark
- `report.py`: Clean up deprecated functions

## Impact

- BacktestResult.plot_portfolio_beta() now works without pre-fetching benchmark data
- Cleaner public API in report.py
- Updated notebooks with beta charts
