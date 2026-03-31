## Context

`summary()` returns 4 metrics. The documented API expects 12+. The `full_summary()` added in Chunk 5 overlaps with some of these. We need to align both with the docs.

Trade records already capture per-trade fees. We need to aggregate them in `_run_single` and pass totals to `_SingleResult`.

## Goals / Non-Goals

**Goals:**
- Expand `summary()` to match `docs/api/index.md` summary table
- Compute total_fee and rebalance_count from trade records
- Refactor `full_summary()` to extend `summary()` (avoid duplication)
- Fix example 02 to use multi-backtest API

**Non-Goals:**
- Not implementing the period returns (mtd, 3m, 6m, ytd, 1y) in this change — those belong to `full_summary()` in a later iteration
- Not changing the trade record structure

## Decisions

### 1. summary() metric order matches docs/api/index.md

The documented order is: risk_free_rate, total_return, cagr, sharpe, sortino, max_drawdown, calmar, kelly, final_value, total_fee, rebalance_count.

**BREAKING**: `sharpe` renamed to `sharpe`. Tests must update.

### 2. Kelly leverage computation

Kelly = `mean(excess_returns) / var(excess_returns)`. When variance is 0, return 0.0. This is the standard Kelly criterion for optimal leverage.

### 3. total_fee and rebalance_count from trade records

In `_run_single`, after accumulating all trade records:
- `total_fee = sum(rec["fee"] for rec in all_trade_records)`
- `rebalance_count = len(set(rec["date"] for rec in all_trade_records))`

Pass both as constructor args to `_SingleResult`.

### 4. full_summary() builds on summary()

`full_summary()` calls `summary()` internally and extends with additional metrics. This avoids duplicating the base metric computation.

## Risks / Trade-offs

- **[BREAKING rename]** — `sharpe` → `sharpe` breaks any code doing `result.summary().loc["sharpe"]`. Mitigation: documented in proposal; the old name was ambiguous.
