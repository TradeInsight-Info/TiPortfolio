## ADDED Requirements

### Requirement: Flexible VIX data input
The system SHALL accept VIX volatility data either as a separate DataFrame parameter or through automatic fetching based on volatility symbol.

#### Scenario: VIX data provided as separate DataFrame
- **WHEN** caller provides `vix_df` parameter to VolatilityBasedEngine.run()
- **THEN** system SHALL use the provided DataFrame directly for VIX series
- **AND** SHALL NOT fetch volatility index data

#### Scenario: VIX data fetched automatically
- **WHEN** caller does not provide `vix_df` but provides volatility_symbol
- **THEN** system SHALL fetch VIX data using fetch_volatility_index()
- **AND** SHALL create VIX series from fetched data

### Requirement: VIX series extraction from separate data
The system SHALL extract VIX series from a separate DataFrame when provided, maintaining the same interface as the current price dict approach.

#### Scenario: Extract VIX from separate DataFrame
- **WHEN** vix_df is provided as a separate DataFrame
- **THEN** system SHALL extract close price series from vix_df
- **AND** SHALL align to trading_dates with forward/backward fill
- **AND** SHALL return pd.Series with trading_dates index

### Requirement: Backward compatibility for VIX data
The system SHALL maintain backward compatibility by supporting the existing approach of including VIX data in the prices dictionary.

#### Scenario: Legacy VIX in prices dict
- **WHEN** VIX symbol is present in prices_df and no separate vix_df is provided
- **THEN** system SHALL extract VIX series from prices_df using current method
- **AND** SHALL behave identically to existing implementation
