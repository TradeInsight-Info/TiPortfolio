## Review

### Consistency Check
- Proposal lists 1 capability (`summary-metrics-alignment`) — spec covers it with 3 requirements.
- All metrics from `docs/api/index.md` summary table are referenced in the spec.

### Completeness Check
- Kelly leverage formula specified (mean_excess / variance).
- total_fee and rebalance_count require trade record accumulation — design addresses this.
- Example 02 fix is straightforward — use existing `ti.run(*tests)` API.
- Metric names `sharpe` and `sortino` kept as-is (annualised). No breaking rename needed.

### Issues Found
None — proposal, brainstorm, and specs are aligned.
