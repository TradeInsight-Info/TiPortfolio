## ADDED Requirements

### Requirement: Never rebalancing schedule
The system SHALL support a "never" schedule identifier that prevents any rebalancing after initial allocation.

#### Scenario: Never schedule produces no rebalance dates
- **WHEN** user creates Schedule("never") for any date range
- **THEN** get_rebalance_dates returns empty DatetimeIndex

#### Scenario: Never schedule implements buy-and-hold strategy
- **WHEN** user runs BacktestEngine with Schedule("never") and FixRatio allocation
- **THEN** backtest produces buy-and-hold results with zero rebalance decisions

#### Scenario: Never schedule works with all engine types
- **WHEN** user creates ScheduleBasedEngine or VolatilityBasedEngine with Schedule("never")
- **THEN** engines run successfully with no rebalancing after initial allocation

#### Scenario: Never schedule handles multi-asset portfolios
- **WHEN** user runs engine with Schedule("never") and multiple assets (e.g., SPY, QQQ, GLD)
- **THEN** system maintains initial allocation weights throughout backtest period

#### Scenario: Never schedule maintains backward compatibility
- **WHEN** existing code uses other schedule types
- **THEN** all existing functionality continues to work unchanged

#### Scenario: Never schedule edge case handling
- **WHEN** user provides invalid parameters with Schedule("never")
- **THEN** system handles gracefully without errors
