## ADDED Requirements

### Requirement: Time-based freezing filter
The system SHALL provide a TimeBasedFilter class that prevents rebalancing within a specified time period after the last rebalance.

#### Scenario: Basic freezing period enforcement
- **WHEN** user creates TimeBasedFilter(freezing_time_days=7) and last rebalance was 3 days ago
- **THEN** filter returns False (no rebalance allowed)

#### Scenario: Freezing period expiration
- **WHEN** user creates TimeBasedFilter(freezing_time_days=7) and last rebalance was 10 days ago
- **THEN** filter returns True (rebalance allowed)

#### Scenario: First rebalance always allowed
- **WHEN** user creates TimeBasedFilter(freezing_time_days=7) and no previous rebalance exists
- **THEN** filter returns True (first rebalance allowed)

#### Scenario: Zero freezing period allows all rebalances
- **WHEN** user creates TimeBasedFilter(freezing_time_days=0)
- **THEN** filter always returns True (no freezing restriction)

#### Scenario: Time-based filter with engine integration
- **WHEN** user runs VolatilityBasedEngine with TimeBasedFilter(freezing_time_days=5) as rebalance_filter
- **THEN** engine only rebalances when both VIX conditions are met AND at least 5 days have passed since last rebalance

#### Scenario: Invalid freezing period handling
- **WHEN** user creates TimeBasedFilter(freezing_time_days=-1)
- **THEN** system raises ValueError with descriptive message

#### Scenario: Time-based filter independence from VIX
- **WHEN** user uses TimeBasedFilter without VIX data
- **THEN** filter functions correctly based only on time constraints

#### Scenario: Calendar day calculation
- **WHEN** freezing period spans weekends and holidays
- **THEN** filter uses calendar days (not trading days) for time calculation
