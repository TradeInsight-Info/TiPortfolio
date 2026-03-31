## Review

### Consistency Check

All 3 capabilities from the proposal map to specs:
- `trades-wrapper` → specs/trades-wrapper/spec.md (4 requirements)
- `full-summary-metrics` → specs/full-summary-metrics/spec.md (5 requirements)
- `chart-enhancements` → specs/chart-enhancements/spec.md (4 requirements)

Brainstorm chunks A/B/C align with the 3 spec capabilities. No gaps.

### Completeness Check

- Trade recording: covers open, adjust, and close scenarios. Equity_before/equity_after enables sample() ranking.
- Full summary: Sortino, Calmar, max DD duration, monthly returns, win rate all specified with edge cases.
- Charts: security weights, histogram, Plotly dispatch all covered. ImportError for missing Plotly specified.
- BacktestResult delegation: both full_summary and chart methods covered for multi-backtest case.

### Issues Found

None. All capabilities consistent, all scenarios testable.
