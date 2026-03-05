## Context

Currently, plotting functionality exists as standalone functions in `tiportfolio.report`:
- `plot_portfolio_with_assets_interactive(result)` 
- Comparison functions

Users must import these functions explicitly and pass `BacktestResult` objects. The `BacktestResult` class in `backtest.py` has no visualization methods.

## Goals / Non-Goals

**Goals:**
- Add `plot_portfolio()` method to `BacktestResult` that replicates `plot_portfolio_with_assets_interactive` behavior
- Add `plot_rolling_book_composition()` for long/short strategy visualization
- Add `plot_portfolio_beta()` for beta tracking
- Maintain backward compatibility with existing standalone functions

**Non-Goals:**
- Rewrite all report.py functions - only move the core visualization methods
- Add matplotlib support (Plotly only for interactive)
- Modify the backtest engine logic

## Decisions

1. **Add methods to BacktestResult dataclass** - Using methods on the result object provides cleaner API than standalone functions. The dataclass can hold plotting state if needed.

2. **Keep backward compatibility** - Standalone functions in report.py will remain but show deprecation warnings. Users can migrate at their own pace.

3. **Use Plotly for all interactive charts** - Consistent with existing `plot_portfolio_with_assets_interactive`. Avoid adding matplotlib as a new dependency.

4. **Store reference to Plotly figure, return it** - Methods return the Plotly figure object for further customization if needed.

## Risks / Trade-offs

- [Risk] Methods bloat the dataclass → [Mitigation] Keep methods focused, extract complex logic to private functions in backtest.py
- [Risk] Breaking change for existing users → [Mitigation] Deprecation warnings, not removal
- [Risk] Beta computation requires benchmark data not in result → [Mitigation] Add optional `benchmark_prices` parameter or compute on-the-fly
