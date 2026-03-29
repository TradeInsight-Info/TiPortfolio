## ADDED Requirements

### Requirement: Signal.Schedule fires on matching trading days
The system SHALL provide `Signal.Schedule` that returns `True` when `context.date` matches the schedule rule. It SHALL use `pandas_market_calendars` NYSE calendar to resolve trading days.

#### Scenario: Monthly end schedule fires on last trading day
- **WHEN** Signal.Schedule is configured for month-end and context.date is the last NYSE trading day of January
- **THEN** `__call__` returns `True`

#### Scenario: Monthly end schedule skips mid-month
- **WHEN** Signal.Schedule is configured for month-end and context.date is January 15 (a trading day, not month-end)
- **THEN** `__call__` returns `False`

### Requirement: Signal.Monthly delegates to Signal.Schedule
The system SHALL provide `Signal.Monthly(day="end", next_trading_day=True)` that internally creates a `Signal.Schedule` and delegates `__call__` to it.

#### Scenario: Monthly fires on month-end trading days
- **WHEN** Signal.Monthly() is called across 60 trading days spanning 3 months
- **THEN** it returns `True` exactly 3 times (once per month-end)

### Requirement: Select.All populates context.selected from children
The system SHALL provide `Select.All` that sets `context.selected = list(context.portfolio.children or [])` and returns `True`.

#### Scenario: Leaf portfolio with ticker children
- **WHEN** Select.All is called with a portfolio whose children are `["QQQ", "BIL", "GLD"]`
- **THEN** `context.selected` becomes `["QQQ", "BIL", "GLD"]`

### Requirement: Weigh.Equally assigns equal weights
The system SHALL provide `Weigh.Equally()` that divides weight equally across `context.selected` and writes to `context.weights`.

#### Scenario: Three selected tickers
- **WHEN** Weigh.Equally() is called with `context.selected = ["QQQ", "BIL", "GLD"]`
- **THEN** `context.weights` becomes `{"QQQ": 1/3, "BIL": 1/3, "GLD": 1/3}` (approximately)

### Requirement: Action.Rebalance triggers trade execution via callback
The system SHALL provide `Action.Rebalance` that checks whether the portfolio is a leaf or parent node and calls the appropriate engine callback (`_execute_leaf` or `_allocate_children`).

#### Scenario: Leaf node rebalance
- **WHEN** Action.Rebalance is called on a leaf portfolio with `_execute_leaf` callback set
- **THEN** `_execute_leaf(portfolio, context)` is called and the algo returns `True`

#### Scenario: Missing callback raises error
- **WHEN** Action.Rebalance is called but `_execute_leaf` callback is None
- **THEN** `RuntimeError` is raised

### Requirement: Action.PrintInfo prints debug information
The system SHALL provide `Action.PrintInfo` that prints the current date and portfolio name, and always returns `True`.

#### Scenario: PrintInfo outputs debug line
- **WHEN** Action.PrintInfo is called with date 2024-01-31 and portfolio name "test"
- **THEN** output contains "[2024-01-31] portfolio=test" and the algo returns `True`
