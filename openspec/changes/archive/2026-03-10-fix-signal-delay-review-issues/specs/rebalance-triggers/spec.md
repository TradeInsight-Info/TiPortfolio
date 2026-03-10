## ADDED Requirements

### Requirement: Calendar schedule signal_delay asymmetry is documented

For calendar-based rebalance schedules (e.g. `month_end`, `quarter_start`), `signal_delay` SHALL NOT be forwarded to `get_rebalance_dates()`. The signal_delay offset SHALL only affect `prices_history` slicing inside the backtest loop. A code comment SHALL document this intentional asymmetry at the `get_rebalance_dates()` call site in `run_backtest()`.

#### Scenario: Calendar schedule rebalance dates are not shifted by signal_delay
- **WHEN** `run_backtest()` is called with a calendar-based schedule and `signal_delay=2`
- **THEN** rebalance dates are the standard calendar dates (e.g. last trading day of each month for `month_end`)
- **AND** `prices_history` on each rebalance day is sliced to 2 trading days before the rebalance date
