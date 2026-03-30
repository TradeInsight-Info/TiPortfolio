## ADDED Requirements

### Requirement: Signal.Quarterly fires on specified months
`Signal.Quarterly` SHALL be an `Algo` subclass that fires `True` on the last trading day of each specified month. Default months SHALL be `[2, 5, 8, 11]` (Feb, May, Aug, Nov).

#### Scenario: Default quarterly months
- **WHEN** `Signal.Quarterly()` is evaluated across a full year of trading days
- **THEN** it returns `True` exactly 4 times — on the last NYSE trading days of Feb, May, Aug, Nov

#### Scenario: Custom months
- **WHEN** `Signal.Quarterly(months=[3, 6, 9, 12])` is evaluated across a full year
- **THEN** it returns `True` exactly 4 times — on the last NYSE trading days of Mar, Jun, Sep, Dec

### Requirement: Signal.Quarterly delegates to Or composition
`Signal.Quarterly` SHALL internally compose `Or(*[Signal.Schedule(month=m, day=day) for m in months])`.

#### Scenario: Internal delegation
- **WHEN** `Signal.Quarterly(months=[2, 5])` is constructed
- **THEN** its internal implementation uses `Or` with two `Schedule` instances

### Requirement: Signal.Schedule supports integer day parameter
`Signal.Schedule(day=int)` SHALL resolve the target day to a valid NYSE trading day. When `next_trading_day=True` (default), it SHALL snap forward to the next valid trading day in the same month. When `next_trading_day=False`, it SHALL return `False` if the target day is not a trading day.

#### Scenario: Integer day on a trading day
- **WHEN** `Signal.Schedule(day=15)` is evaluated on a date where the 15th is a NYSE trading day
- **THEN** it returns `True`

#### Scenario: Integer day on a non-trading day with next_trading_day=True
- **WHEN** `Signal.Schedule(day=15, next_trading_day=True)` is evaluated in a month where the 15th is a Saturday
- **THEN** it returns `True` on the following Monday (the next NYSE trading day)

#### Scenario: Integer day on a non-trading day with next_trading_day=False
- **WHEN** `Signal.Schedule(day=15, next_trading_day=False)` is evaluated in a month where the 15th is a Saturday
- **THEN** it returns `False` for that entire month

#### Scenario: Integer day exceeds month length
- **WHEN** `Signal.Schedule(day=31)` is evaluated in February
- **THEN** it returns `False` (no valid trading day at or after the 31st in Feb)
