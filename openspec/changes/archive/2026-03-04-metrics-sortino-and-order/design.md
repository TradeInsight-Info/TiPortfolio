## Context

`compute_metrics()` in `metrics.py` currently returns: `sharpe_ratio`, `cagr`, `max_drawdown`, `mar_ratio`, `kelly_leverage`. The `compare_strategies()` function in `report.py` iterates over `_COMPARE_METRICS = ("sharpe_ratio", "cagr", "max_drawdown", "mar_ratio", "final_value", "kelly_leverage", "total_fee")`.

Two metrics are missing: **Sortino ratio** (penalises only downside volatility, unlike Sharpe) and **mean excess return** (annualised daily excess return — a building block for both ratios). The current metric ordering is not conventional, and comparison shows all 7 metrics when only the top 5 are actionable.

## Goals / Non-Goals

**Goals:**
- Add `mean_excess_return` and `sortino_ratio` to `compute_metrics()` return value
- Reorder the metrics dict so canonical order is: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, then `kelly_leverage`
- Update `BacktestResult.summary()` to display the two new metrics and respect new order
- Restrict `compare_strategies()` to the top 5 metrics: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`

**Non-Goals:**
- Changing how existing metrics are calculated
- Adding new engine or allocation logic
- Changing `rebalance_decisions_table` or chart functions

## Decisions

**Sortino ratio formula**

Sortino = (annualised mean excess return) / (annualised downside deviation)

- Downside deviation: `std` of returns below the daily risk-free rate (not zero), annualised with `sqrt(252)`
- When there are no negative excess returns, Sortino = `nan` (not `inf`) to keep downstream code safe
- Annualised mean excess return = `excess.mean() * periods_per_year`
- Alternative considered: use target return = 0. Rejected — consistency with Sharpe (which already uses `risk_free_rate`) is more important.

**`mean_excess_return` as a separate metric**

Expose it explicitly rather than only as an intermediate. It is a useful standalone signal (absolute return above risk-free) and makes the Sortino calculation transparent.

**Metric ordering**

Return dict order in Python 3.7+ is insertion-ordered. Build the return dict in the desired order:
`sharpe_ratio → sortino_ratio → mar_ratio → cagr → max_drawdown → kelly_leverage → mean_excess_return`

`mean_excess_return` goes last (supporting metric rather than primary signal).

**`compare_strategies` top-5 restriction**

Replace `_COMPARE_METRICS` tuple with the 5 primary metrics:
`("sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown")`

`sortino_ratio`: higher is better (same direction as `sharpe_ratio`).
Remove `final_value`, `kelly_leverage`, `total_fee` from comparison — they remain accessible via `result.metrics` and `result.total_fee` but are not in the comparison table.

## Risks / Trade-offs

- [Risk] Tests asserting on the `metrics` dict keys or order will break → Mitigation: update all affected tests as part of this change
- [Risk] Tests asserting on `compare_strategies` row count or index names will break → Mitigation: update `test_report.py`
- [Trade-off] Removing `final_value`, `kelly_leverage`, `total_fee` from `compare_strategies` narrows the comparison — accepted since the goal is focused comparison; full data remains on the result object
- [Risk] `sortino_ratio` returns `nan` when downside std = 0 (e.g. equity-only bull run with no down days) → Mitigation: same `nan` guard already used for Sharpe; callers should handle `nan`
