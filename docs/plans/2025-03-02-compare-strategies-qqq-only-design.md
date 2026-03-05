# Compare Strategies and QQQ-Only Design

**Date:** 2025-03-02

## Purpose

- Add a second strategy in the start-of-month rebalance notebook: hold only QQQ (no rebalancing).
- Ensure the engine produces empty rebalance decisions when there is a single asset.
- Add a compare function to compare two backtest results side-by-side and use it to verify whether the 70/20/10 QQQ/BIL/GLD rebalance strategy is better than holding 100% QQQ.

## 1. Engine: Single-Asset, No Rebalance Decisions

When the allocation has only one symbol (e.g. 100% QQQ), the strategy is buy-and-hold. Rebalancing is meaningless, so `rebalance_decisions` must be empty.

**Current behavior:** With one symbol the engine still enters the rebalance block on each schedule date; trades are zero and fees zero, but it appends a `RebalanceDecision` every time.

**Change:** In `_run_backtest` (`src/tiportfolio/engine.py`), only append to `decisions` when `len(symbols) > 1`. Keep all other logic (mark-to-market, target_dollars, trades, fee_paid, updating positions_dollars and total_equity) unchanged so the loop remains correct. Single-asset backtests get the correct equity curve and metrics; `rebalance_decisions` is always empty.

## 2. Notebook: QQQ-Only Strategy and Compare

**Flow:**

1. Existing: Load data (QQQ, BIL, GLD), run backtest with WEIGHTS 70/20/10 and `Schedule("month_start")`, store as `result` (or `result_rebalance`). Print summary.
2. New cell: QQQ-only. Build `prices_qqq = {"QQQ": prices["QQQ"]}`. Engine with `FixRatio(weights={"QQQ": 1.0})`, same schedule and fee/initial_value. Run, store as `result_qqq_only`. Print `result_qqq_only.summary()`.
3. New cell: Call `compare_strategies(result, result_qqq_only, name_a="70/20/10 QQQ/BIL/GLD", name_b="100% QQQ")` and display the returned DataFrame.

Config (SYMBOLS, START, END, INITIAL_VALUE) stays in the first cell; no second data load.

## 3. Report: compare_strategies API

**Signature:**

```python
def compare_strategies(
    result_a: BacktestResult,
    result_b: BacktestResult,
    *,
    name_a: str = "Strategy A",
    name_b: str = "Strategy B",
) -> pd.DataFrame
```

**Output:** DataFrame with one row per metric (`sharpe_ratio`, `cagr`, `max_drawdown`, `mar_ratio`), two value columns (name_a, name_b). Optional third column indicating which strategy is better per metric (higher Sharpe/CAGR/MAR better; lower max_drawdown better). Implement in `tiportfolio.report`; add to package `__init__.py` if desired for public API.

## 4. Error Handling and Testing

- **Engine:** No new validation; single-asset is valid. Only skip appending to `decisions` when `len(symbols) == 1`.
- **compare_strategies:** Assume both results have the same metric keys; missing keys yield NaN. No extra validation unless desired.

**Tests:**

- **Engine:** Add test (e.g. in `test_engine.py`) that runs a single-asset backtest over a range that includes rebalance dates; assert `len(result.rebalance_decisions) == 0` and that metrics are finite.
- **compare_strategies:** Add test that builds two minimal BacktestResult (equity_curve + metrics), calls `compare_strategies`, and asserts DataFrame shape, column names, and that values match input metrics.
