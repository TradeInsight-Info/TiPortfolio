## ADDED Requirements

### Requirement: signal_delay must be non-negative

`BacktestEngine.__init__()` SHALL reject a `signal_delay` value less than zero by raising `ValueError` with a descriptive message indicating the received value.

#### Scenario: Negative signal_delay raises ValueError at construction
- **WHEN** `ScheduleBasedEngine(allocation=..., rebalance=..., signal_delay=-1)` is called
- **THEN** `ValueError` is raised immediately, before any data is fetched or backtest runs
- **AND** the error message SHALL include the invalid value

#### Scenario: signal_delay=0 is accepted
- **WHEN** `BacktestEngine` subclass is constructed with `signal_delay=0`
- **THEN** no error is raised and `self.signal_delay == 0`

#### Scenario: Positive signal_delay is accepted
- **WHEN** `BacktestEngine` subclass is constructed with `signal_delay=2`
- **THEN** no error is raised and `self.signal_delay == 2`
