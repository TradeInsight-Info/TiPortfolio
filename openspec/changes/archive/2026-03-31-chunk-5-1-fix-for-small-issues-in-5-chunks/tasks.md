> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Track Fees and Rebalances

- [x] 1.1 Modify `_run_single` in `backtest.py` to compute `total_fee` and `rebalance_count` from accumulated trade records, pass to `_SingleResult`
- [x] 1.2 Update `_SingleResult.__init__` to accept and store `total_fee` and `rebalance_count`

## 2. Expand summary() Metrics

- [x] 2.1 Expand `summary()` to return all documented metrics: risk_free_rate, total_return, cagr, sharpe, sortino, max_drawdown, calmar, kelly, final_value, total_fee, rebalance_count
- [x] 2.2 Refactor `full_summary()` to call `summary()` internally and extend (avoid duplication)
- [x] 2.3 Update `tests/test_result.py` — fix assertions for renamed `sharpe` → `sharpe`, add checks for new metric keys
- [x] 2.4 Update `tests/test_result_full.py` — fix any assertions that reference old metric names
- [x] 2.5 Run tests to verify

## 3. Fix Example 02

- [x] 3.1 Rewrite `examples/02_custom_config.py` to use `ti.run(bt_low, bt_high, bt_big)` and print `result.summary()` for side-by-side comparison

## 4. Integration

- [x] 4.1 Run full test suite to verify no regressions
