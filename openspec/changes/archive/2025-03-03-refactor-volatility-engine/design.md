## Context

The current VolatilityBasedEngine has several design issues:
1. Parameter naming inconsistency (`dfs_in_dict` vs `prices_df`)
2. VIX data is tightly coupled with price data in the same dict
3. run_backtest receives engine-specific parameters, breaking abstraction
4. VIX series extraction happens inside the engine rather than being configurable

The codebase has two engine types (ScheduleBasedEngine and VolatilityBasedEngine) that both inherit from BacktestEngine but have different data handling patterns.

## Goals / Non-Goals

**Goals:**
- Standardize parameter naming across engines (`prices_df`)
- Enable flexible VIX data input (separate DataFrame or automatic fetching)
- Decouple run_backtest from engine-specific implementation details
- Improve code reusability and maintainability

**Non-Goals:**
- Changing the core backtest algorithm
- Modifying allocation strategy interfaces
- Breaking existing functionality (only API changes)

## Decisions

**Parameter Naming Standardization**
- Rename `dfs_in_dict` to `prices_df` across all engines for consistency
- This aligns with internal variable naming and improves readability

**VIX Data Handling**
- Add optional `vix_df` parameter to VolatilityBasedEngine.run()
- If `vix_df` provided, use it directly; otherwise fetch using volatility_symbol
- Keep backward compatibility by supporting both approaches

**run_backtest Decoupling**
- Remove engine-specific parameters (rebalance_filter, vix_series, context_for_date, schedule_kwargs)
- These should be handled by individual engines before calling run_backtest
- Makes run_backtest truly engine-agnostic

**VIX Series Extraction**
- Modify `_vix_series_from_prices` to work with separate VIX DataFrame
- Create unified interface for VIX data regardless of source

## Risks / Trade-offs

**Breaking Changes** → Migration path needed for existing code
- Risk: Existing code using `dfs_in_dict` will break
- Mitigation: Clear error messages and documentation updates

**Complexity** → More flexible but slightly more complex interface
- Risk: Multiple ways to provide VIX data could confuse users
- Mitigation: Clear documentation and examples showing preferred approach

**Performance** → Minimal impact
- Risk: Additional parameter checking might add slight overhead
- Mitigation: Negligible impact compared to data fetching costs
