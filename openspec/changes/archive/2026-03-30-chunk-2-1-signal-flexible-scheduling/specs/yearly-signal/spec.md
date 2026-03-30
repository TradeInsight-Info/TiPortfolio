## ADDED Requirements

### Requirement: Signal.Yearly fires once per year with period-level day resolution
`Signal.Yearly` SHALL be an `Algo` subclass that fires once per year. The `day` parameter SHALL resolve at **year** level: `"start"` targets January, `"mid"` targets July, `"end"` targets December.

#### Scenario: Default (end of year)
- **WHEN** `Signal.Yearly()` is evaluated across a full year of trading days
- **THEN** it fires exactly once — on the last NYSE trading day of December

#### Scenario: Start of year
- **WHEN** `Signal.Yearly(day="start")` is evaluated across a full year
- **THEN** it fires exactly once — on the first NYSE trading day of January

#### Scenario: Mid-year
- **WHEN** `Signal.Yearly(day="mid")` is evaluated across a full year
- **THEN** it fires exactly once — on the first NYSE trading day on or after July 1

#### Scenario: Integer day with explicit month
- **WHEN** `Signal.Yearly(day=15, month=6)` is evaluated across a full year
- **THEN** it fires exactly once — on the first NYSE trading day on or after June 15

### Requirement: Signal.Yearly accepts optional month override
When `day` is an `int` or when the user wants to override the default month, an optional `month` parameter SHALL specify which month to fire in.

#### Scenario: Custom month with end
- **WHEN** `Signal.Yearly(day="end", month=6)` is evaluated
- **THEN** it fires on the last trading day of June (overrides default December)

#### Scenario: Custom month with start
- **WHEN** `Signal.Yearly(day="start", month=4)` is evaluated
- **THEN** it fires on the first trading day of April (overrides default January)
