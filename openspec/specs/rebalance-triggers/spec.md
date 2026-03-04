# Purpose

TBD

## Requirements

### Requirement: Scheduled rebalance every Monday

The system SHALL support scheduled rebalance every Monday, with dates aligned to nearest NYSE trading days.

#### Scenario: Monday rebalance dates generated
- **WHEN** schedule is set to "weekly_monday" and trading dates span multiple Mondays
- **THEN** rebalance dates include each Monday adjusted to the closest trading day

### Requirement: Scheduled rebalance every Wednesday

The system SHALL support scheduled rebalance every Wednesday, with dates aligned to nearest NYSE trading days.

#### Scenario: Wednesday rebalance dates generated
- **WHEN** schedule is set to "weekly_wednesday" and trading dates span multiple Wednesdays
- **THEN** rebalance dates include each Wednesday adjusted to the closest trading day

### Requirement: Scheduled rebalance every Friday

The system SHALL support scheduled rebalance every Friday, with dates aligned to nearest NYSE trading days.

#### Scenario: Friday rebalance dates generated
- **WHEN** schedule is set to "weekly_friday" and trading dates span multiple Fridays
- **THEN** rebalance dates include each Friday adjusted to the closest trading day

### Requirement: Scheduled rebalance never

The system SHALL support a "never" rebalance schedule that performs no rebalancing.

#### Scenario: No rebalance dates for never schedule
- **WHEN** schedule is set to "never"
- **THEN** empty DatetimeIndex is returned for rebalance dates

### Requirement: Volatility rebalance with freezing time

The system SHALL support volatility-based rebalance with a configurable freezing period in days to prevent rebalancing if the last rebalance occurred within that period.

#### Scenario: Rebalance skipped due to freezing
- **WHEN** VIX triggers rebalance but last rebalance was within freezing days
- **THEN** the rebalance is not performed

#### Scenario: Rebalance allowed after freezing period
- **WHEN** VIX triggers rebalance and last rebalance was more than freezing days ago
- **THEN** the rebalance is performed
