## Review

### Consistency Check
- Proposal lists one new capability `run-aip` — specs contain exactly one spec file `specs/run-aip/spec.md`. Consistent.
- Proposal says "identical summary/plot interface" — spec Requirement "Result compatibility" covers all methods (`summary`, `full_summary`, `plot`, `plot_security_weights`, `trades`). Consistent.
- Proposal says "AIP-specific metrics: total_contributions, contribution_count" — spec Requirement "AIP-specific summary metrics" covers both. Consistent.
- Proposal says no modified capabilities — correct, `run()` and existing result infrastructure are unchanged.

### Completeness Check
- All 6 requirements have scenarios with WHEN/THEN format. All are testable.
- Edge case covered: first trading day (no injection).
- Edge case covered: injection on non-rebalance day (cash waits).
- Edge case covered: injection on rebalance day (full equity used).

### Issues Found

1. **Month-end detection method not specified**: The spec says "last trading day of each calendar month" but doesn't specify how to detect this. Implementation should check if the next trading day is in a different month. This is an implementation detail for design.md — not a spec gap.

2. **Initial capital handling**: The spec says "portfolio begins with initial_capital only" on the first day. This is consistent with how `run()` works today. No issue.

3. **Summary metric placement**: The spec adds `total_contributions` and `contribution_count` to `summary()`. This means `_SingleResult` needs to accept these values. The existing `_SingleResult` class doesn't have these fields, so design.md should specify how to add them without breaking the existing constructor.

No blocking issues. Ready for design.
