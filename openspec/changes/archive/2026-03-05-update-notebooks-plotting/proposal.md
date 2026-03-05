## Why

The previous change added plotting methods directly to `BacktestResult` class (`plot_portfolio()`, `plot_rolling_book_composition()`, `plot_portfolio_beta()`). Now we need to update the Jupyter notebooks to use these new methods instead of the deprecated standalone functions, and add the new beta chart to all relevant notebooks.

## What Changes

1. Update all notebooks to use `result.plot_portfolio()` instead of `plot_portfolio_with_assets_interactive(result)`
2. Add beta chart (`result.plot_portfolio_beta()`) to all notebooks that have long/short strategies
3. Add rolling book composition chart to notebooks that use BetaScreenerStrategy or similar long/short strategies
4. Remove deprecated function imports from notebooks

## Capabilities

### Modified Capabilities
- `beta-neutral-notebook`: Update to use new plotting methods, add beta chart
- `dollar-neutral-notebook`: Update to use new plotting methods, add beta chart
- `volatility-targeting-notebook`: Update to use new plotting methods (no beta for long-only)

## Impact

- **Notebooks to update:**
  - `notebooks/beta_neutral_dynamic.ipynb`
  - `notebooks/dollar_neutral_txn_kvue.ipynb`
  - `notebooks/volatility_targeting_qqq_bil_gld.ipynb`
  - `notebooks/start_of_month_rebalance.ipynb`
  - `notebooks/vix_target_rebalance.ipynb`
- **API Usage**: Replace deprecated `plot_portfolio_with_assets_interactive(result)` with `result.plot_portfolio()`
