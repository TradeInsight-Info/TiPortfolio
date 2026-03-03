## Why

The VolatilityBasedEngine has parameter naming inconsistencies and tight coupling with run_backtest that makes it difficult to reuse across different engine types. The current design mixes data preparation concerns with backtest execution, reducing modularity and making the codebase harder to maintain.

## What Changes

- **BREAKING**: Rename `dfs_in_dict` parameter to `prices_df` in both ScheduleBasedEngine and VolatilityBasedEngine for clarity
- **BREAKING**: Refactor VIX series handling to accept a separate `vix_df` parameter instead of extracting from prices dict
- **BREAKING**: Remove engine-specific parameters from run_backtest calls to improve reusability
- Add optional `vix_df` parameter to VolatilityBasedEngine.run() method
- Modify VIX series extraction to work with separate VIX DataFrame when provided
- Clean up run_backtest interface to be engine-agnostic

## Capabilities

### New Capabilities
- `vix-data-handling`: Flexible VIX data input handling for volatility-based engines

### Modified Capabilities
- `volatility-engine`: Refactor parameter interface and VIX data handling

## Impact

- **Code**: src/tiportfolio/engine.py (ScheduleBasedEngine, VolatilityBasedEngine)
- **Code**: src/tiportfolio/backtest.py (run_backtest function signature)
- **API**: Breaking changes to engine.run() method signatures
- **Compatibility**: Existing code using dfs_in_dict parameter will need updates
