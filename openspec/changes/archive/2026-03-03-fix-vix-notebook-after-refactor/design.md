## Context

The VIX target rebalance notebook (`notebooks/vix_target_rebalance.ipynb`) was broken by the volatility engine refactor. The refactor moved VIX regime logic from `VixRegimeAllocation` class to `VolatilityBasedEngine` class, changing the API surface:

- **Before**: `VixRegimeAllocation` required `target_vix`, `lower_bound`, `upper_bound` parameters
- **After**: `VixRegimeAllocation` only requires allocation strategies, VIX parameters moved to engine

The notebook still uses the old API, causing a `TypeError` when trying to instantiate `VixRegimeAllocation`.

## Goals / Non-Goals

**Goals:**
- Fix the notebook to work with the refactored API
- Ensure the notebook produces the same VIX regime strategy results as before
- Add documentation comments explaining the API change for future reference
- Verify all notebook cells execute successfully

**Non-Goals:**
- Change the underlying VIX regime logic or strategy behavior
- Modify the engine refactor implementation
- Add new features to the notebook

## Decisions

**Minimal API Fix Approach**: 
- **Why**: The engine parameters in the notebook appear correct, only the constructor call needs fixing
- **Alternative**: Could rewrite the entire notebook, but that's unnecessary and risky
- **Decision**: Fix only the broken constructor call and add explanatory comments

**Preserve Existing Results**:
- **Why**: Users rely on the notebook's output for strategy comparison
- **Alternative**: Could accept different results if API changes affected behavior
- **Decision**: Ensure the fix produces identical results to the original working version

## Risks / Trade-offs

**[Risk]** API confusion for users who see old examples → **Mitigation**: Add clear comments explaining the refactor change
**[Risk]** Notebook might have other hidden dependencies on old API → **Mitigation**: Test all cells thoroughly after fix
**[Trade-off]** Minimal fix vs comprehensive documentation → **Decision**: Prioritize working notebook, add targeted documentation
