## Why

The `summary()` output currently returns only 4 metrics (total_return, cagr, max_drawdown, sharpe), but `docs/index.md` and `docs/api/index.md` document 12+ metrics including Sortino, Calmar, Kelly Leverage, Final Value, Total Fee, and Rebalance Count. Additionally, example 02 runs 3 separate `ti.run()` calls instead of demonstrating the multi-backtest `ti.run(bt1, bt2, bt3)` API that already exists.

## What Changes

- **Expand `summary()`**: Add all metrics documented in `docs/api/index.md` — Sortino, Calmar, Kelly, final_value, total_fee, rebalance_count, risk_free_rate, start/end dates
- **Track fees and rebalances**: Modify `_run_single` in `backtest.py` to accumulate total fees and rebalance count from trade records, pass to `_SingleResult`
- **Align `full_summary()`**: Build on expanded `summary()` to avoid duplication
- **Fix example 02**: Use `ti.run(bt_low, bt_high, bt_big)` for proper side-by-side comparison

## Capabilities

### New Capabilities

- `summary-metrics-alignment`: Align `summary()` and `full_summary()` output with the documented API spec

### Modified Capabilities

_(none)_

## Impact

- **Code**: `result.py` (expanded `summary()`), `backtest.py` (fee/rebalance tracking)
- **Tests**: `test_result.py` needs updated assertions for new summary keys
- **Examples**: `02_custom_config.py` simplified to use multi-backtest API
- Metric names `sharpe` and `sortino` are kept as-is (annualised). No breaking rename.
