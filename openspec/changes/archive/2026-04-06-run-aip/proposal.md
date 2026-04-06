## Why

Many retail investors use auto investment plans (AIP / dollar-cost averaging) — contributing a fixed amount monthly into their portfolio. TiPortfolio currently only supports lump-sum backtesting via `run()`. Adding `run_aip()` lets users simulate how a regular savings plan would have performed with their strategy, which is a more realistic scenario for most retail users.

## What Changes

- Add `run_aip()` public function that accepts the same `Backtest` objects as `run()` plus a `monthly_aip_amount` parameter
- Modify the simulation loop to inject cash at month-end trading days before the algo stack fires
- Return `BacktestResult` with identical `summary()`, `full_summary()`, `plot()` interface
- Add AIP-specific metrics to summary: `total_contributions`, `contribution_count`
- Export `run_aip` from the public API

## Capabilities

### New Capabilities
- `run-aip`: Auto Investment Plan simulation — monthly cash injection into portfolio with allocation based on current strategy weights. Includes contribution tracking and standard performance metrics.

### Modified Capabilities
_None — existing `run()` and result infrastructure remain unchanged._

## Impact

- **Code**: `src/tiportfolio/backtest.py` (new function), `src/tiportfolio/__init__.py` (export)
- **APIs**: New public function `run_aip()` — additive, no breaking changes
- **Tests**: New `tests/test_aip.py`
- **Examples**: New `examples/21_auto_investment_plan.py`
- **Dependencies**: None — uses existing pandas/numpy stack
