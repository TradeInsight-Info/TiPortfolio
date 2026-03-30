# Schedule Day Modes

**Purpose**: Defines the `day` parameter modes and `closest_trading_day` behaviour for `Signal.Schedule`.

## Requirements

### Requirement: Signal.Schedule accepts "start" day mode
When `day="start"`, Schedule SHALL target day 1 of the month and search **forward** to the first NYSE trading day.

#### Scenario: First day is a trading day
- **WHEN** `Signal.Schedule(day="start")` is evaluated on January 2, 2024 (Tuesday, first trading day of Jan)
- **THEN** it returns `True`

#### Scenario: First day is a weekend
- **WHEN** `Signal.Schedule(day="start")` is evaluated in a month where day 1 is Saturday
- **THEN** it returns `True` on Monday (the first trading day) and `False` on all other days

#### Scenario: Start with month filter
- **WHEN** `Signal.Schedule(day="start", month=3)` is evaluated in January
- **THEN** it returns `False` (wrong month)

### Requirement: Signal.Schedule accepts "mid" day mode
When `day="mid"`, Schedule SHALL target day 15 of the month and search **forward** to the first NYSE trading day on or after that date. Same search direction as `"start"` and `int`.

#### Scenario: Day 15 is a trading day
- **WHEN** `Signal.Schedule(day="mid")` is evaluated on a month where the 15th is a Wednesday
- **THEN** it returns `True` on the 15th

#### Scenario: Day 15 is a Saturday — forward search
- **WHEN** `Signal.Schedule(day="mid")` is evaluated in a month where the 15th is a Saturday
- **THEN** it returns `True` on Monday the 17th (next trading day forward)

#### Scenario: Day 15 is a Sunday — forward search
- **WHEN** `Signal.Schedule(day="mid")` is evaluated in a month where the 15th is a Sunday
- **THEN** it returns `True` on Monday the 16th (next trading day forward)

### Requirement: Signal.Schedule "end" mode unchanged
When `day="end"`, Schedule SHALL search **backward** from the last calendar day to find the last NYSE trading day. Existing behavior preserved.

#### Scenario: Backward search
- **WHEN** `Signal.Schedule(day="end")` is evaluated in January 2024
- **THEN** it returns `True` on January 31 (Wednesday, last trading day)

### Requirement: Signal.Schedule closest_trading_day parameter
The parameter `closest_trading_day` (default `True`) controls snap behaviour. When `False`, the signal SHALL only fire if the exact target day is a NYSE trading day.

#### Scenario: closest_trading_day=True (default)
- **WHEN** `Signal.Schedule(day=15, closest_trading_day=True)` is evaluated and the 15th is a Saturday
- **THEN** it fires on the next trading day (Monday the 17th)

#### Scenario: closest_trading_day=False strict mode
- **WHEN** `Signal.Schedule(day=15, closest_trading_day=False)` is evaluated and the 15th is a Saturday
- **THEN** it returns `False` for the entire month (no snap)

#### Scenario: closest_trading_day with "mid" mode
- **WHEN** `Signal.Schedule(day="mid", closest_trading_day=False)` is evaluated and day 15 is a Saturday
- **THEN** it returns `False` (strict — no forward search)
