## Why

The VIX target rebalance notebook is broken due to the volatility engine refactor that moved VIX regime logic from `VixRegimeAllocation` to `VolatilityBasedEngine`. The notebook still uses the old API where `VixRegimeAllocation` constructor required VIX parameters that are now handled by the engine.

## What Changes

- **Fix VixRegimeAllocation constructor**: Remove the missing `target_vix`, `lower_bound`, and `upper_bound` parameters that are no longer part of the API
- **Verify engine parameters**: Ensure the `VolatilityBasedEngine.run()` call has the correct VIX parameters (already appears correct)
- **Test notebook execution**: Verify the notebook runs successfully and produces expected results
- **Update documentation**: Add comments explaining the API change for future reference

## Capabilities

### New Capabilities
- `vix-notebook`: Fix broken VIX target rebalance notebook to work with refactored engine

### Modified Capabilities
- None (this is a fix, not a capability change)

## Impact

- **Code**: `notebooks/vix_target_rebalance.ipynb` (fix constructor call)
- **Documentation**: Add explanatory comments about API change
- **User Experience**: Restore working example of VIX-based rebalancing strategy
