## ADDED Requirements

### Requirement: Select all by default
When `--select` is not specified, the CLI SHALL use `Select.All()`.

#### Scenario: Default selection
- **WHEN** no `--select` flag is passed
- **THEN** the backtest SHALL use `Select.All()`

### Requirement: Select all explicitly
`--select all` SHALL use `Select.All()`.

#### Scenario: Explicit all
- **WHEN** `--select all` is passed
- **THEN** the backtest SHALL use `Select.All()`

### Requirement: Select momentum
`--select momentum` SHALL use `Select.Momentum(n=, lookback=)` with `--top-n` and `--lookback` options.

#### Scenario: Momentum with top-3
- **WHEN** `--select momentum --top-n 3 --lookback 90d` is passed
- **THEN** the backtest SHALL use `Select.Momentum(n=3, lookback=pd.DateOffset(days=90))`

#### Scenario: Momentum requires --top-n
- **WHEN** `--select momentum` is passed without `--top-n`
- **THEN** an error SHALL indicate that `--top-n` is required with momentum selection
