# Quarterly Signal

**Purpose**: Defines `Signal.Monthly` and `Signal.Quarterly` behaviour, including the `closest_trading_day` parameter and day-mode pass-through.

## Requirements

### Requirement: Signal.Monthly closest_trading_day parameter
`Signal.Monthly` constructor SHALL accept `closest_trading_day: bool = True`, passing through to `Signal.Schedule`.

#### Scenario: Monthly with closest_trading_day
- **WHEN** `Signal.Monthly(day=15, closest_trading_day=False)` is constructed
- **THEN** it delegates to `Signal.Schedule(day=15, closest_trading_day=False)`

### Requirement: Signal.Quarterly supports start/mid/end day modes
`Signal.Quarterly` SHALL pass the `day` parameter through to each `Schedule` instance. The day modes resolve at the **monthly** level within each quarterly month. Default months are `[1, 4, 7, 10]`.

#### Scenario: Quarterly default (end) behavior
- **WHEN** `Signal.Quarterly()` is evaluated
- **THEN** it fires on the last trading day of Jan, Apr, Jul, Oct

#### Scenario: Quarterly with day="start"
- **WHEN** `Signal.Quarterly(day="start")` is evaluated across a full year
- **THEN** it fires 4 times — on the first trading day of Jan, Apr, Jul, Oct

#### Scenario: Quarterly with day="mid"
- **WHEN** `Signal.Quarterly(day="mid")` is evaluated across a full year
- **THEN** it fires 4 times — on the first trading day on or after the 15th of Jan, Apr, Jul, Oct

#### Scenario: Quarterly with int day
- **WHEN** `Signal.Quarterly(day=10)` is evaluated across a full year
- **THEN** it fires 4 times — on the first trading day on or after the 10th of Jan, Apr, Jul, Oct

### Requirement: Signal.Quarterly inherits closest_trading_day
`Signal.Quarterly` delegates to `Schedule` which uses `closest_trading_day`. No constructor change needed since `Quarterly` passes `day` to `Schedule`.

#### Scenario: Quarterly strict mode
- **WHEN** `Signal.Quarterly(day=15)` is evaluated with default `closest_trading_day=True`
- **THEN** it fires on the first trading day on or after the 15th of Jan, Apr, Jul, Oct
