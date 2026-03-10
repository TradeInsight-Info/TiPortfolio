## 1. Validate signal_delay in BacktestEngine

- [x] 1.1 In `src/tiportfolio/engine.py` `BacktestEngine.__init__()`, add guard: `if signal_delay < 0: raise ValueError(f"signal_delay must be >= 0; got {signal_delay}")`
- [x] 1.2 Remove the no-op self-assignment `context_for_date = context_for_date` from `engine.py`

## 2. Fix VIX context test to actually verify signal_date is used

- [x] 2.1 Redesign `TestVixContextUsesSignalDate` VIX fixture in `tests/test_signal_delay.py` so VIX at signal_date (crossing day) differs from VIX at execution_date (crossing day + 1)
- [x] 2.2 Update the assertion to check that the `vix_at_date` passed to `get_target_weights` for the triggered rebalance equals the signal-date VIX value (not the execution-date value)

## 3. Fix legacy behavior test to verify behavioral equivalence

- [x] 3.1 Update `test_signal_delay_zero_reproduces_legacy_behavior` in `tests/test_signal_delay.py` to use a fixture that actually triggers at least one rebalance (e.g. enough trading days to cross a month boundary or trigger a VIX crossing)
- [x] 3.2 Assert that rebalance decision dates in the `signal_delay=0` result match expected known dates (not just `is not None`)

## 4. Fix broken engine subclass test

- [x] 4.1 Remove the broken `run()` override from `TestSignalDelayParameter::test_backtest_engine_accepts_signal_delay` in `tests/test_signal_delay.py` — only assert `engine.signal_delay == 2`

## 5. Document calendar schedule asymmetry

- [x] 5.1 Add a comment in `src/tiportfolio/backtest.py` at the `get_rebalance_dates()` call site explaining that `signal_delay` is intentionally not forwarded for calendar schedules (only used for `prices_history` slicing)

## 6. Fix broken test collection

- [x] 6.1 Delete `tests/allocations/test_vix_targeting.py` (imports from non-existent modules `tiportfolio.portfolio.allocation.allocation` and `tiportfolio.portfolio.allocation.frequency_based_allocation`, blocking test suite collection)
- [x] 6.2 Delete `src/tiportfolio/portfolio/allocation/vix_targeting.py` (orphaned source file whose own imports fail — same missing modules)

## 7. Verify

- [x] 7.1 Run `uv run pytest -v` and confirm all tests pass with no collection errors
- [x] 7.2 Run `uv run mypy src/` and confirm no new type errors introduced
