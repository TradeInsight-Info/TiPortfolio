## MODIFIED Requirements

### Requirement: Parameter naming consistency
All engine run() methods SHALL use consistent parameter naming for price data input.

#### Scenario: ScheduleBasedEngine parameter rename
- **WHEN** calling ScheduleBasedEngine.run()
- **THEN** parameter SHALL be named `prices_df` instead of `dfs_in_dict`
- **AND** SHALL accept dict[str, pd.DataFrame] with same behavior

#### Scenario: VolatilityBasedEngine parameter rename
- **WHEN** calling VolatilityBasedEngine.run()
- **THEN** parameter SHALL be named `prices_df` instead of `dfs_in_dict`
- **AND** SHALL accept dict[str, pd.DataFrame] with same behavior

### Requirement: Engine-agnostic run_backtest interface
The run_backtest function SHALL not receive engine-specific parameters and SHALL be reusable across different engine types.

#### Scenario: Clean run_backtest call
- **WHEN** any engine calls run_backtest()
- **THEN** call SHALL only include universal parameters: prices_df, allocation, schedule_spec, fee_per_share, start, end, initial_value
- **AND** SHALL NOT include rebalance_filter, vix_series, context_for_date, schedule_kwargs
- **AND** engines SHALL handle engine-specific logic before calling run_backtest

### Requirement: VolatilityBasedEngine VIX data flexibility
VolatilityBasedEngine.run() SHALL accept an optional vix_df parameter for VIX data input.

#### Scenario: Separate VIX DataFrame provided
- **WHEN** vix_df parameter is provided to VolatilityBasedEngine.run()
- **THEN** system SHALL use vix_df for VIX series extraction
- **AND** SHALL ignore VIX data in prices_df if present

#### Scenario: No separate VIX DataFrame provided
- **WHEN** vix_df parameter is None
- **THEN** system SHALL extract VIX series from prices_df using volatility_symbol
- **AND** SHALL behave identically to current implementation
