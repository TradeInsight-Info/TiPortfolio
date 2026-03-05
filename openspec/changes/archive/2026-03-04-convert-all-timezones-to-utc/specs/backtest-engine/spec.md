## MODIFIED Requirements

### Requirement: BacktestEngine run method normalizes timezones to UTC

The BacktestEngine.run method SHALL normalize all price DataFrame datetime indices to UTC timezone before processing backtests, ensuring consistent time references regardless of input data timezone.

#### Scenario: Price data normalized to UTC during backtest
- **WHEN** BacktestEngine.run is called with price DataFrames containing datetime indices
- **THEN** all datetime indices are converted to UTC timezone before backtest calculations

#### Scenario: Mixed timezone data handled correctly
- **WHEN** price DataFrames have datetime indices in different timezones (including DST-affected zones)
- **THEN** all indices are converted to UTC consistently without time shifts
