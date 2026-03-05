## Context

The previous change refactored plotting functions to be methods on `BacktestResult`. Now we need to update Jupyter notebooks to use these new APIs. This is a documentation/update task across multiple notebooks.

## Goals / Non-Goals

**Goals:**
- Update all notebooks to use `result.plot_portfolio()` instead of deprecated `plot_portfolio_with_assets_interactive(result)`
- Add beta charts to notebooks with long/short strategies
- Add rolling book composition charts where applicable
- Remove deprecated imports from notebooks

**Non-Goals:**
- Rewrite notebook logic - only update plotting calls
- Add new analysis - just add the new visualizations
- Change strategy implementations

## Decisions

1. **Keep existing imports alongside new ones** - Add the new method calls while keeping existing structure. The new methods are backwards compatible.

2. **Beta chart requires benchmark data** - For `plot_portfolio_beta()`, we need to fetch benchmark prices (SPY). Add this as a new cell in relevant notebooks.

3. **Book composition only for long/short** - Only add `plot_rolling_book_composition()` to notebooks using BetaScreenerStrategy or DollarNeutral

4. **Run all cells after changes** - Verify notebooks still execute without errors after updates

## Risks / Trade-offs

- [Risk] Notebooks may fail after updates → [Mitigation] Run each notebook after changes to verify
- [Risk] Beta data may not be available → [Mitigation] Add try/except or fetch SPY prices explicitly
