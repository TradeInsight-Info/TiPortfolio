## Purpose

CLI `--aip` option for auto investment plan simulation. Adds a shared `--aip <amount>` flag to all CLI subcommands (monthly, quarterly, weekly, yearly, every, once) that routes to `run_aip()` instead of `run()`, injecting a fixed cash amount on the last trading day of each month.

## Requirements

### Requirement: --aip option available on all subcommands
The CLI SHALL accept an optional `--aip <amount>` flag on all subcommands (monthly, quarterly, weekly, yearly, every, once). The amount is a positive float representing the monthly cash injection.

#### Scenario: Monthly with AIP
- **WHEN** user runs `tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --aip 1000`
- **THEN** the CLI runs an AIP backtest with $1,000 monthly contributions and prints summary including `total_contributions` and `contribution_count`

#### Scenario: AIP with other subcommands
- **WHEN** user runs `tiportfolio quarterly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --aip 500`
- **THEN** the CLI runs an AIP backtest with quarterly rebalancing and $500 monthly contributions

#### Scenario: AIP omitted
- **WHEN** user runs `tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31` without `--aip`
- **THEN** the CLI runs a standard lump-sum backtest with no contribution metrics in the output

### Requirement: AIP with leverage
The CLI SHALL support combining `--aip` with `--leverage`.

#### Scenario: AIP and leverage together
- **WHEN** user runs `tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --aip 1000 --leverage 1.5`
- **THEN** the CLI runs an AIP backtest with leverage applied

### Requirement: AIP help text
The `--aip` option SHALL appear in `--help` output with a clear description.

#### Scenario: Help displays AIP option
- **WHEN** user runs `tiportfolio monthly --help`
- **THEN** the output includes `--aip` with help text describing monthly cash injection amount
