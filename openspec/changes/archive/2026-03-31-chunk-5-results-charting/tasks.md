> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Trade Recording

- [x] 1.1 Write tests for trade recording: new position, adjusted position, closed position, trade record columns
- [x] 1.2 Modify `execute_leaf_trades` in `backtest.py` to return `list[dict]` of trade records
- [x] 1.3 Modify `_run_single` to accumulate trade records and pass to `_SingleResult`
- [x] 1.4 Add weight recording: capture `context.weights` at each rebalance for `plot_security_weights`
- [x] 1.5 Run trade recording tests

## 2. Trades Wrapper

- [x] 2.1 Write tests for `Trades` class: DataFrame delegation (`head`, `describe`, column access), `sample(n)`, sample with overlap deduplication
- [x] 2.2 Implement `Trades` class in `result.py` with `__getattr__` and `__getitem__` delegation
- [x] 2.3 Implement `Trades.sample(n)` with nlargest/nsmallest + deduplication
- [x] 2.4 Add `trades` property to `_SingleResult`
- [x] 2.5 Run Trades tests

## 3. Full Summary Metrics

- [x] 3.1 Write tests for `full_summary()`: Sortino, max DD duration, Calmar, best/worst month, win rate
- [x] 3.2 Implement `full_summary()` on `_SingleResult`
- [x] 3.3 Implement `full_summary()` on `BacktestResult` (side-by-side comparison)
- [x] 3.4 Run full_summary tests

## 4. Chart Enhancements

- [x] 4.1 Write tests for `plot_security_weights()` (returns Figure), `plot_histogram()` (returns Figure)
- [x] 4.2 Implement `plot_security_weights()` on `_SingleResult` (stacked area from weight_history)
- [x] 4.3 Implement `plot_histogram()` on `_SingleResult` (daily return distribution)
- [x] 4.4 Implement `plot(interactive=True)` with lazy Plotly import and ImportError fallback
- [x] 4.5 Add `plot_security_weights()` and `plot_histogram()` to `BacktestResult` with delegation
- [x] 4.6 Run chart tests

## 5. Examples

- [x] 5.1 Create `examples/17_full_results.py` — single backtest: print `full_summary()`, print `trades.sample(3)`, save `plot_security_weights()` and `plot_histogram()` charts. Use `csv=CSV_DATA`
- [x] 5.2 Create `examples/18_multi_backtest_comparison.py` — two strategies (equal-weight vs ratio), `ti.run(bt1, bt2)`, print side-by-side `summary()` and `full_summary()`, save overlaid `plot()`. Use `csv=CSV_DATA`

## 6. Integration

- [x] 6.1 Run full test suite to verify no regressions
- [x] 6.2 Verify multi-backtest comparison works end-to-end (summary + full_summary + plots)
