## Why

The `signal_delay` implementation added to prevent look-ahead bias in backtesting has several correctness gaps identified in code review: negative values silently re-introduce look-ahead bias, a key test does not actually verify the VIX context uses `signal_date`, and a broken test file prevents the full test suite from collecting. These gaps reduce confidence in the fix and could hide regressions.

## What Changes

- Add validation to reject negative `signal_delay` values with a clear error
- Redesign the VIX context test so signal_date and execution_date have different VIX values, and assert the correct signal-date VIX is used
- Fix the `test_signal_delay_zero_reproduces_legacy_behavior` test to verify actual behavioral equivalence (rebalance dates and weights), not just a non-None result
- Fix the `TestBacktestEngineAcceptsSignalDelay` test to remove the broken `_run_with_prices()` call that would raise `AttributeError`
- Add a clarifying comment at the `get_rebalance_dates()` call in `run_backtest()` explaining why `signal_delay` is not forwarded for calendar schedules
- Remove the no-op `context_for_date = context_for_date` self-assignment in `engine.py`
- Fix the broken test collection error in `tests/allocations/test_vix_targeting.py` caused by orphaned imports referencing non-existent modules

## Capabilities

### New Capabilities

- `signal-delay-validation`: Validates that `signal_delay >= 0` at engine construction time, raising `ValueError` on negative values

### Modified Capabilities

- `backtest-engine`: Add validation constraint — `signal_delay` must be non-negative
- `rebalance-triggers`: Clarify that `signal_delay` is not applied to calendar-based rebalance date calculation (only to `prices_history` slicing)

## Impact

- `src/tiportfolio/engine.py` — add `signal_delay` validation in `BacktestEngine.__init__()`, remove no-op self-assignment
- `src/tiportfolio/backtest.py` — add comment explaining asymmetric `signal_delay` behavior for calendar schedules
- `tests/test_signal_delay.py` — fix three tests: VIX context test, legacy behavior test, engine subclass test
- `tests/allocations/test_vix_targeting.py` — remove or skip orphaned test file that imports non-existent modules
