## MODIFIED Requirements

### Requirement: Engine signal_delay Threading

`BacktestEngine.__init__()` SHALL accept an optional `signal_delay: int` parameter (default `1`) and store it as an instance attribute. It SHALL be passed through to `run_backtest()`. Values less than `0` SHALL raise `ValueError`.

#### Scenario: ScheduleBasedEngine passes signal_delay
- **WHEN** `ScheduleBasedEngine(signal_delay=2)` is constructed and `run()` is called
- **THEN** `run_backtest()` SHALL receive `signal_delay=2`

#### Scenario: VolatilityBasedEngine passes signal_delay
- **WHEN** `VolatilityBasedEngine(signal_delay=1)` is constructed and `run()` is called
- **THEN** both `get_rebalance_dates()` and `run_backtest()` SHALL receive `signal_delay=1`

#### Scenario: Negative signal_delay raises ValueError at construction
- **WHEN** any BacktestEngine subclass is constructed with `signal_delay=-1`
- **THEN** `ValueError` is raised with a message including the invalid value
