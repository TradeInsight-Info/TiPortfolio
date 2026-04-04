## Purpose

Defines the CLI subcommands for each rebalancing signal type: monthly, quarterly, weekly, yearly, every (N-period), and once (buy-and-hold).

## Requirements

### Requirement: Monthly subcommand
`tiportfolio monthly` SHALL create a `Signal.Monthly(day=)` signal.

#### Scenario: Monthly with default day
- **WHEN** `tiportfolio monthly --tickers QQQ,BIL --start 2020-01-01 --end 2024-12-31 --ratio equal`
- **THEN** the backtest SHALL use `Signal.Monthly(day="end")`

#### Scenario: Monthly with start-of-month
- **WHEN** `--day start` is passed
- **THEN** the signal SHALL be `Signal.Monthly(day="start")`

### Requirement: Quarterly subcommand
`tiportfolio quarterly` SHALL create a `Signal.Quarterly(months=, day=)` signal.

#### Scenario: Quarterly with defaults
- **WHEN** `tiportfolio quarterly --tickers QQQ,BIL --start 2020-01-01 --end 2024-12-31 --ratio equal`
- **THEN** the signal SHALL use `Signal.Quarterly()` with default months `[1,4,7,10]` and day `"end"`

#### Scenario: Quarterly with custom months
- **WHEN** `--months 3,6,9,12` is passed
- **THEN** the signal SHALL use `Signal.Quarterly(months=[3,6,9,12])`

### Requirement: Weekly subcommand
`tiportfolio weekly` SHALL create a `Signal.Weekly(day=)` signal.

#### Scenario: Weekly with default day
- **WHEN** `tiportfolio weekly --tickers QQQ --start 2020-01-01 --end 2024-12-31 --ratio equal`
- **THEN** the signal SHALL use `Signal.Weekly(day="end")`

### Requirement: Yearly subcommand
`tiportfolio yearly` SHALL create a `Signal.Yearly(day=, month=)` signal.

#### Scenario: Yearly with defaults
- **WHEN** `tiportfolio yearly --tickers QQQ --start 2020-01-01 --end 2024-12-31 --ratio equal`
- **THEN** the signal SHALL use `Signal.Yearly()` with defaults

#### Scenario: Yearly with custom month
- **WHEN** `--month 6` is passed
- **THEN** the signal SHALL use `Signal.Yearly(month=6)`

### Requirement: Every subcommand
`tiportfolio every` SHALL create a `Signal.EveryNPeriods(n=, period=, day=)` signal.

#### Scenario: Every 5 days
- **WHEN** `tiportfolio every --n 5 --period day --tickers QQQ --start 2020-01-01 --end 2024-12-31 --ratio equal`
- **THEN** the signal SHALL use `Signal.EveryNPeriods(n=5, period="day")`

#### Scenario: Every requires --n and --period
- **WHEN** `tiportfolio every` is run without `--n` or `--period`
- **THEN** an error SHALL be shown indicating the missing required options

### Requirement: Once subcommand
`tiportfolio once` SHALL create a `Signal.Once()` signal for buy-and-hold.

#### Scenario: Once buy-and-hold
- **WHEN** `tiportfolio once --tickers QQQ --start 2020-01-01 --end 2024-12-31 --ratio equal`
- **THEN** the signal SHALL use `Signal.Once()`
