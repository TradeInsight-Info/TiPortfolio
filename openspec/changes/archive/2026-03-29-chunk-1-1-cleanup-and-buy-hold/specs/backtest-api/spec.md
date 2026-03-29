## MODIFIED Requirements

### Requirement: Backtest constructor accepts config only
The system SHALL provide `Backtest(portfolio, data, config=None)`. The `fee_per_share` convenience parameter is removed. Fees SHALL be set exclusively via `TiConfig(fee_per_share=...)`.

#### Scenario: Valid construction with default config
- **WHEN** `Backtest(portfolio, data)` is called
- **THEN** the Backtest uses `TiConfig()` with default fees

#### Scenario: Custom fees via TiConfig
- **WHEN** `Backtest(portfolio, data, config=TiConfig(fee_per_share=0.01))` is called
- **THEN** the Backtest uses fee_per_share=0.01

## REMOVED Requirements

### Requirement: fee_per_share parameter on Backtest
**Reason**: Redundant — TiConfig already holds this value. Single source of truth.
**Migration**: Replace `Backtest(portfolio, data, fee_per_share=0.01)` with `Backtest(portfolio, data, config=TiConfig(fee_per_share=0.01))`
