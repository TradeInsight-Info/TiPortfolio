## ADDED Requirements

### Requirement: Weekly Monday rebalancing schedule
The system SHALL support rebalancing every Monday using the "weekly_mon" schedule identifier.

#### Scenario: Monday schedule generates correct dates
- **WHEN** user creates Schedule("weekly_mon") for date range 2024-01-01 to 2024-01-31
- **THEN** system generates rebalance dates for all Mondays in that range (2024-01-01, 2024-01-08, 2024-01-15, 2024-01-22, 2024-01-29)

#### Scenario: Monday schedule aligns to trading days
- **WHEN** Monday falls on a market holiday
- **THEN** system aligns rebalance to closest trading day using existing NYSE calendar logic

### Requirement: Weekly Wednesday rebalancing schedule
The system SHALL support rebalancing every Wednesday using the "weekly_wed" schedule identifier.

#### Scenario: Wednesday schedule generates correct dates
- **WHEN** user creates Schedule("weekly_wed") for date range 2024-01-01 to 2024-01-31
- **THEN** system generates rebalance dates for all Wednesdays in that range (2024-01-03, 2024-01-10, 2024-01-17, 2024-01-24, 2024-01-31)

### Requirement: Weekly Friday rebalancing schedule
The system SHALL support rebalancing every Friday using the "weekly_fri" schedule identifier.

#### Scenario: Friday schedule generates correct dates
- **WHEN** user creates Schedule("weekly_fri") for date range 2024-01-01 to 2024-01-31
- **THEN** system generates rebalance dates for all Fridays in that range (2024-01-05, 2024-01-12, 2024-01-19, 2024-01-26)

### Requirement: Weekly Monday-Wednesday-Friday rebalancing schedule
The system SHALL support rebalancing on Monday, Wednesday, and Friday using the "weekly_mon_wed_fri" schedule identifier.

#### Scenario: Mon-Wed-Fri schedule generates correct dates
- **WHEN** user creates Schedule("weekly_mon_wed_fri") for date range 2024-01-01 to 2024-01-31
- **THEN** system generates rebalance dates for all Mon/Wed/Fri in that range (2024-01-01, 2024-01-03, 2024-01-05, 2024-01-08, 2024-01-10, 2024-01-12, 2024-01-15, 2024-01-17, 2024-01-19, 2024-01-22, 2024-01-24, 2024-01-26, 2024-01-29, 2024-01-31)

#### Scenario: Weekly schedules work with all engine types
- **WHEN** user creates BacktestEngine with Schedule("weekly_mon")
- **THEN** engine runs backtest with Monday rebalancing and produces valid results

#### Scenario: Weekly schedules maintain backward compatibility
- **WHEN** existing code uses monthly/quarterly/yearly schedules
- **THEN** all existing functionality continues to work unchanged
