## ADDED Requirements

### Requirement: Kelly leverage calculation in metrics
The system SHALL provide Kelly leverage calculation in the performance metrics output for optimal position sizing guidance.

#### Scenario: Kelly leverage included in metrics output
- **WHEN** compute_metrics function is executed with valid equity data
- **THEN** the returned metrics dictionary SHALL include 'kelly_leverage' key
- **AND** kelly_leverage SHALL be calculated as annualized_mean_excess_return / (annualized_std_dev ** 2)

#### Scenario: Kelly leverage with insufficient data
- **WHEN** compute_metrics is called with equity data having fewer than 2 data points
- **THEN** kelly_leverage SHALL be float('nan')

#### Scenario: Kelly leverage with zero variance
- **WHEN** equity returns have zero variance
- **THEN** kelly_leverage SHALL be float('nan')

### Requirement: Annualized Sharpe ratio confirmation
The system SHALL ensure Sharpe ratio calculation is properly annualized using the provided periods_per_year parameter.

#### Scenario: Sharpe ratio annualization
- **WHEN** compute_metrics calculates Sharpe ratio
- **THEN** Sharpe ratio SHALL be annualized as (excess_return_mean / excess_return_std) * sqrt(periods_per_year)
- **AND** SHALL use the provided risk_free_rate for excess return calculation
