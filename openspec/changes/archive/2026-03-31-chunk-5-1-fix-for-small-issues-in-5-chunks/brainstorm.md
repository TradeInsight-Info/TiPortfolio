# Chunk 5.1: Fix Summary Metrics + Example 02

**Goal**: Align `summary()` output with the documented API, and fix example 02 to use multi-backtest `ti.run()`.

**Architecture**: Modify `result.py` to expand `summary()` with all documented metrics. Modify `backtest.py` to track total fees and rebalance count. Fix example 02.

**Tech Stack**: Python 3.12, pandas, tiportfolio

**Spec**: `docs/index.md` (Get Started summary output), `docs/api/index.md` (summary() key table)

## File Map

1. Modify: `src/tiportfolio/result.py` — Expand `summary()` to include all documented metrics (Sortino, Calmar, Kelly, final_value, total_fee, rebalance_count)
2. Modify: `src/tiportfolio/backtest.py` — Track total fees and rebalance count in `_run_single`, pass to `_SingleResult`
3. Modify: `examples/02_custom_config.py` — Use `ti.run(bt_low, bt_high, bt_big)` for side-by-side comparison
4. Modify: `tests/test_result.py` — Update tests for new summary metrics

## Chunks

### Chunk A: Expand summary() metrics

Current `summary()` returns 4 metrics. Documented API expects ~12. Need to add:
- `sharpe` (annualised Sharpe ratio)
- `sortino` (annualised Sortino ratio)
- `calmar` (CAGR / |max_drawdown|)
- `kelly` (Kelly leverage = mean_excess / variance)
- `final_value` (last equity value)
- `total_fee` (sum of all trade fees)
- `rebalance_count` (number of distinct rebalance dates)
- `risk_free_rate` (from config)
- `start` / `end` dates

Files:
- `src/tiportfolio/result.py`
- `src/tiportfolio/backtest.py`
- `tests/test_result.py`

Steps:
- Add total_fee and rebalance_count tracking to `_run_single`
- Pass them to `_SingleResult.__init__`
- Expand `summary()` to include all documented metrics
- Update `full_summary()` to build on expanded `summary()`

### Chunk B: Fix example 02

Replace 3 separate `ti.run()` calls with one `ti.run(bt_low, bt_high, bt_big)`.

Files:
- `examples/02_custom_config.py`

Steps:
- Use `result = ti.run(bt_low, bt_high, bt_big)`
- Print `result.summary()` for side-by-side comparison
