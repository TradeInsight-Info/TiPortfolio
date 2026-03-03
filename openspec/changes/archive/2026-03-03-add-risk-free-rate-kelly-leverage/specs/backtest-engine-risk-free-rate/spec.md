## ADDED Requirements

### Requirement: BacktestEngine risk-free rate configuration
The system SHALL allow BacktestEngine classes to be initialized with a risk_free_rate parameter for accurate excess return calculations.

#### Scenario: Default risk-free rate initialization
- **WHEN** a BacktestEngine instance is created without specifying risk_free_rate
- **THEN** the engine SHALL use 0.04 as the default risk-free rate

#### Scenario: Custom risk-free rate initialization
- **WHEN** a BacktestEngine instance is created with risk_free_rate=0.03
- **THEN** the engine SHALL use 0.03 as the risk-free rate for all calculations

#### Scenario: Risk-free rate used in metrics
- **WHEN** engine calculates performance metrics
- **THEN** risk-free rate SHALL be passed to compute_metrics function for Sharpe ratio calculation
