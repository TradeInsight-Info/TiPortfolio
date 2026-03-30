## ADDED Requirements

### Requirement: Signal.EveryNPeriods fires every N-th period
`Signal.EveryNPeriods` SHALL be a stateful `Algo` subclass that fires on a configured day every N-th period boundary. It SHALL accept `n: int`, `period: str` (`"day"` | `"week"` | `"month"` | `"year"`), and `day: str | int` (default `"end"`).

#### Scenario: Biweekly (every 2 weeks)
- **WHEN** `Signal.EveryNPeriods(n=2, period="week")` is evaluated across 8 weeks of trading days
- **THEN** it fires 4 times — on the last trading day of every 2nd week

#### Scenario: Every 3 months
- **WHEN** `Signal.EveryNPeriods(n=3, period="month")` is evaluated across 12 months
- **THEN** it fires 4 times — on the last trading day of every 3rd month

#### Scenario: Every 2 days
- **WHEN** `Signal.EveryNPeriods(n=2, period="day")` is evaluated across 10 trading days
- **THEN** it fires 5 times — on every 2nd trading day

#### Scenario: Day parameter controls which day in the period
- **WHEN** `Signal.EveryNPeriods(n=2, period="week", day="start")` is evaluated
- **THEN** it fires on the first trading day of every 2nd week

### Requirement: Signal.EveryNPeriods resets per backtest
The internal counter SHALL be set during `__init__`, so each `Backtest` with a new `Portfolio` starts fresh.

#### Scenario: Two separate backtests
- **WHEN** two separate `Backtest` objects use portfolios with the same `EveryNPeriods` configuration
- **THEN** each backtest's signal counter starts from zero independently

### Requirement: Signal.EveryNPeriods fires on first eligible period
The signal SHALL fire on the first period boundary encountered (counter starts at N-1 so the first period fires immediately).

#### Scenario: First period fires
- **WHEN** `EveryNPeriods(n=2, period="week")` starts evaluating from the beginning of the data
- **THEN** it fires on the target day of the first week, then skips one week, then fires again
