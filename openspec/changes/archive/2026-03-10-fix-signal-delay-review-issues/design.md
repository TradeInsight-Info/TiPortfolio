## Context

The `signal_delay` feature was added to `backtest.py`, `engine.py`, and `calendar.py` to prevent look-ahead bias. A code review identified correctness and test-quality gaps. All changes are internal to the backtesting library; no public API signatures change (new validation raises `ValueError` for previously-accepted invalid input).

Current state:
- `BacktestEngine.__init__()` accepts `signal_delay: int = 1` with no range validation
- `tests/test_signal_delay.py::TestVixContextUsesSignalDate` passes vacuously — the test fixture has identical VIX at signal_date and execution_date
- `tests/test_signal_delay.py::TestSignalDelayParameter::test_signal_delay_zero_reproduces_legacy_behavior` only asserts result is not None
- `tests/test_signal_delay.py::TestSignalDelayParameter::test_backtest_engine_accepts_signal_delay` defines a broken `run()` override (references non-existent `_run_with_prices`) that is never called
- `tests/allocations/test_vix_targeting.py` imports from `tiportfolio.portfolio.allocation.allocation` and `tiportfolio.portfolio.allocation.frequency_based_allocation`, which do not exist — blocks full test suite collection

## Goals / Non-Goals

**Goals:**
- `signal_delay < 0` raises `ValueError` at engine construction with a clear message
- VIX context test fixture has different VIX values at signal_date vs execution_date; test asserts the signal-date value is used
- Legacy behavior test compares rebalance decision dates between `signal_delay=0` run and a known reference, not just `is not None`
- Engine subclass test removes the broken `_run_with_prices()` call
- Calendar schedule asymmetry is documented with a comment in `run_backtest()`
- Full test suite (`uv run pytest`) collects and passes with no errors

**Non-Goals:**
- Changing `signal_delay` semantics for calendar schedules (intentionally not forwarded to `get_rebalance_dates()`)
- Fixing the `no-redef` mypy error in `calendar.py` (pre-existing, out of scope)
- Implementing the missing `tiportfolio.portfolio.allocation.allocation` module (orphaned code, not part of the active library)

## Decisions

**1. Validate `signal_delay >= 0` in `BacktestEngine.__init__()` only**

The three engine classes all call `super().__init__()` which is `BacktestEngine.__init__()`. Validating once there is sufficient and avoids duplicating the check. `_vix_regime_rebalance_dates()` uses `signal_delay` only with valid values after this point.

Alternative considered: validate at `run_backtest()` call site — rejected because it delays the error past construction, which is worse UX.

**2. Fix `test_vix_regime_allocation_receives_signal_date_context` by redesigning the VIX fixture**

The VIX series must differ between `signal_date` (the crossing day) and `execution_date` (signal_date + 1). Set VIX to cross the threshold at index `i`, then ensure index `i` and `i+1` have meaningfully different VIX values. Assert that the `vix_at_date` passed to `get_target_weights` for the triggered rebalance equals the signal-date VIX, not the execution-date VIX.

**3. Fix `test_signal_delay_zero_reproduces_legacy_behavior` by asserting rebalance decision dates**

Instead of checking `result is not None`, run two backtests with fixtures that actually trigger a rebalance, then assert that the set of rebalance decision dates in the `signal_delay=0` result matches expected dates. This verifies that `signal_delay=0` does not shift execution dates.

**4. Remove broken `run()` override from `TestBacktestEngineAcceptsSignalDelay`**

The test's goal is to verify that `ScheduleBasedEngine` stores `signal_delay` as an attribute. The `run()` override is unnecessary for this and references a non-existent method. Remove it; the constructor assertion is sufficient.

**5. Delete (or skip) `tests/allocations/test_vix_targeting.py`**

The file imports symbols from `tiportfolio.portfolio.allocation.allocation` and other modules that do not exist in the current codebase. This is orphaned code from a different module structure. Since the missing modules are not part of the active library and would require significant work to recreate (out of scope), the test file should be deleted to restore test collection.

Alternative: add a `pytest.importorskip` guard — rejected because the imports fail at module level before any `pytest` code runs.

## Risks / Trade-offs

- [Signal_delay validation is a breaking change for code passing negative values] → Low risk: negative values were always semantically wrong; no legitimate use case exists
- [Deleting test_vix_targeting.py removes coverage for VixTargetingAllocation] → The corresponding source file (`src/tiportfolio/portfolio/allocation/vix_targeting.py`) is also orphaned (its own imports fail). Both should be tracked for cleanup separately.
