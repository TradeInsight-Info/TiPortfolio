## ADDED Requirements

### Requirement: run_aip function signature
The system SHALL provide a `run_aip()` function that accepts one or more `Backtest` objects, a `monthly_aip_amount` float parameter, and an optional `leverage` parameter. The function SHALL return a `BacktestResult`.

#### Scenario: Basic AIP call
- **WHEN** user calls `ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=1000)`
- **THEN** system returns a `BacktestResult` with equity curve, summary, and plot methods

#### Scenario: Multiple backtests with AIP
- **WHEN** user calls `ti.run_aip(bt1, bt2, monthly_aip_amount=1000)`
- **THEN** system returns a `BacktestResult` containing results for both backtests, each with the same monthly contribution amount

#### Scenario: AIP with leverage
- **WHEN** user calls `ti.run_aip(bt, monthly_aip_amount=1000, leverage=1.5)`
- **THEN** system applies leverage to the AIP backtest result identically to how `run()` applies leverage

### Requirement: Monthly cash injection at month-end
The system SHALL inject `monthly_aip_amount` into the root portfolio's cash on the last trading day of each calendar month, before the algo stack evaluates.

#### Scenario: Cash injected on last trading day of month
- **WHEN** the simulation reaches the last trading day of a calendar month
- **THEN** the system adds `monthly_aip_amount` to `portfolio.cash` and `portfolio.equity` before the algo queue fires

#### Scenario: No injection on non-month-end days
- **WHEN** the simulation processes a trading day that is not the last trading day of its calendar month
- **THEN** no additional cash is injected

#### Scenario: First trading day
- **WHEN** the simulation starts on the first trading day
- **THEN** the portfolio begins with `initial_capital` only — no AIP injection on the first day regardless of whether it is a month-end

### Requirement: Allocation of injected cash
The injected cash SHALL be allocated according to the portfolio's current strategy when the algo stack fires on the same day or on the next rebalance date.

#### Scenario: AIP injection on a rebalance day
- **WHEN** monthly cash is injected on a day that the Signal algo also fires
- **THEN** the rebalance uses the full equity (existing + new cash) to compute target positions

#### Scenario: AIP injection on a non-rebalance day
- **WHEN** monthly cash is injected on a month-end day where the Signal algo does not fire
- **THEN** the cash sits in `portfolio.cash` until the next rebalance allocates it

### Requirement: AIP-specific summary metrics
The `BacktestResult` from `run_aip()` SHALL include additional metrics: `total_contributions` (sum of all AIP injections) and `contribution_count` (number of injections made).

#### Scenario: Summary includes contribution metrics
- **WHEN** user calls `result.summary()` on an AIP backtest result
- **THEN** the DataFrame includes `total_contributions` and `contribution_count` rows in addition to all standard metrics

#### Scenario: Contribution tracking accuracy
- **WHEN** a 3-year AIP backtest completes with monthly_aip_amount=1000
- **THEN** `total_contributions` SHALL equal approximately `1000 * number_of_month_ends_in_period` and `contribution_count` SHALL equal the number of month-end trading days

### Requirement: Result compatibility
The `BacktestResult` returned by `run_aip()` SHALL support all the same methods as `run()`: `summary()`, `full_summary()`, `plot()`, `plot_security_weights()`, `trades`.

#### Scenario: Plot works on AIP result
- **WHEN** user calls `result.plot()` on an AIP backtest result
- **THEN** the equity curve chart renders showing the growth including contributions

#### Scenario: Trades accessible on AIP result
- **WHEN** user calls `result.trades` on an AIP backtest result
- **THEN** a Trades DataFrame is returned containing all trade records from the simulation

### Requirement: Public API export
The `run_aip` function SHALL be exported from `tiportfolio` package so users can call `ti.run_aip()`.

#### Scenario: Import run_aip
- **WHEN** user writes `from tiportfolio import run_aip`
- **THEN** the import succeeds and `run_aip` is callable
