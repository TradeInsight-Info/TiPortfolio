# Weekly Signal

**Purpose**: Defines `Signal.Weekly` — fires once per ISO week on a configured day.

## Requirements

### Requirement: Signal.Weekly fires once per week
`Signal.Weekly` SHALL be an `Algo` subclass that fires on a configured day within each ISO week. It SHALL accept a `day` parameter: `"start"` | `"mid"` | `"end"` (default `"end"`).

#### Scenario: Default end-of-week
- **WHEN** `Signal.Weekly()` is evaluated across a full month of trading days
- **THEN** it fires once per week, on the last NYSE trading day of each week (typically Friday)

#### Scenario: Start of week
- **WHEN** `Signal.Weekly(day="start")` is evaluated across a full month
- **THEN** it fires on the first NYSE trading day of each week (typically Monday)

#### Scenario: Mid-week
- **WHEN** `Signal.Weekly(day="mid")` is evaluated across a full month
- **THEN** it fires on the first trading day on or after Wednesday each week

#### Scenario: Short week (holiday Monday)
- **WHEN** `Signal.Weekly(day="start")` is evaluated in a week where Monday is a holiday
- **THEN** it fires on Tuesday (the first trading day of that week)

### Requirement: Signal.Weekly accepts closest_trading_day parameter
`Signal.Weekly` SHALL accept `closest_trading_day: bool = True`, consistent with `Signal.Schedule`.

#### Scenario: closest_trading_day=False on holiday
- **WHEN** `Signal.Weekly(day="start", closest_trading_day=False)` is evaluated in a week where Monday is a holiday
- **THEN** it returns `False` for that entire week
