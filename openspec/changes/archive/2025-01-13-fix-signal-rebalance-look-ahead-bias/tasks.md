## 1. Core Backtest Loop: Signal Delay Parameter

- [x] 1.1 Add `signal_delay: int = 1` parameter to `run_backtest()` in `backtest.py`
- [x] 1.2 Compute `signal_date` as `trading_dates[max(0, current_idx - signal_delay)]` on each rebalance day
- [x] 1.3 Change `prices_history` from `prices_df.loc[:date]` to `prices_df.loc[:signal_date]` on rebalance days
- [x] 1.4 Pass `signal_date=signal_date` in context kwargs to `get_target_weights()`
- [x] 1.5 Ensure `prices_row` remains `prices_df.loc[date]` (execution day close prices, unchanged)
- [x] 1.6 Handle edge case: first rebalance where `signal_date` would be before first trading day (clamp to first date)

## 2. VIX Regime Rebalance Date Shifting

- [x] 2.1 Add `signal_delay: int = 1` parameter to `get_rebalance_dates()` in `calendar.py`
- [x] 2.2 In `_vix_regime_rebalance_dates()`, shift each detected crossing date by `signal_delay` trading days forward using index offset
- [x] 2.3 Discard shifted dates that fall outside the `trading_dates` range
- [x] 2.4 Deduplicate shifted rebalance dates (consecutive crossings may map to same execution day)

## 3. Engine: Thread signal_delay Through

- [x] 3.1 Add `signal_delay: int = 1` to `BacktestEngine.__init__()` and store as instance attribute
- [x] 3.2 Pass `signal_delay` from `ScheduleBasedEngine.run()` to `run_backtest()`
- [x] 3.3 Pass `signal_delay` from `VolatilityBasedEngine.run()` to both `get_rebalance_dates()` and `run_backtest()`
- [x] 3.4 In `VolatilityBasedEngine` rebalance_filter path: defer filter-triggered rebalances by `signal_delay` trading days (queue the execution date, not the signal date)

## 4. VIX Context for Delayed Execution

- [x] 4.1 In `VolatilityBasedEngine.context_for_date()`, use `vix_ser.asof(signal_date)` instead of `vix_ser.asof(date)` when generating context on delayed execution days
- [x] 4.2 Ensure `VixRegimeAllocation` receives VIX context from the signal date, not the execution date

## 5. Tests: Signal Delay Correctness

- [x] 5.1 Write test: `run_backtest(signal_delay=0)` produces identical results to current (pre-fix) behavior
- [x] 5.2 Write test: `run_backtest(signal_delay=1)` — `prices_history` passed to allocation ends at T (not T+1) on rebalance day T+1
- [x] 5.3 Write test: VIX regime crossing on day T produces rebalance on T+1 (not T) with `signal_delay=1`
- [x] 5.4 Write test: VIX crossing on last trading day produces no rebalance with `signal_delay=1`
- [x] 5.5 Write test: `VixChangeFilter` fires on day T, rebalance executes on T+1 with `signal_delay=1`
- [x] 5.6 Write test: VolatilityTargeting lookback window ends at signal_date, not execution_date
- [x] 5.7 Write test: BetaNeutral beta estimation window ends at signal_date
- [x] 5.8 Write test: DollarNeutral receives `signal_date` in context kwargs
- [x] 5.9 Write test: Calendar-based schedules (month_end) are unaffected by `signal_delay`

## 6. Existing Test Updates

- [x] 6.1 Run full test suite and identify tests that fail due to changed default behavior
- [x] 6.2 Update affected test assertions to match corrected (bias-free) output, or pin them to `signal_delay=0` where they test other behavior
- [x] 6.3 Verify all tests pass with `uv run pytest`
