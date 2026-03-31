## ADDED Requirements

### Requirement: full_summary includes Sortino ratio

`_SingleResult.full_summary()` SHALL include the Sortino ratio, computed as annualised excess return divided by downside deviation (using only negative excess returns). SHALL use `config.risk_free_rate` and `config.bars_per_year`.

#### Scenario: Portfolio with downside deviation
- **WHEN** `full_summary()` is called on a result with negative returns
- **THEN** the Sortino ratio SHALL be computed using downside-only deviation

#### Scenario: No negative returns
- **WHEN** all excess returns are non-negative
- **THEN** Sortino SHALL be reported as 0.0 (no downside risk)

### Requirement: full_summary includes max drawdown duration

`_SingleResult.full_summary()` SHALL include max drawdown duration as the number of bars between the drawdown peak and recovery (or end of series if no recovery).

#### Scenario: Drawdown recovers
- **WHEN** the equity curve drops and later recovers to a new high
- **THEN** max drawdown duration SHALL be the number of bars from peak to recovery

#### Scenario: Drawdown never recovers
- **WHEN** the equity curve ends in a drawdown without recovery
- **THEN** max drawdown duration SHALL be the number of bars from peak to end of series

### Requirement: full_summary includes Calmar ratio

`_SingleResult.full_summary()` SHALL include the Calmar ratio, computed as CAGR divided by the absolute value of max drawdown.

#### Scenario: Positive CAGR with drawdown
- **WHEN** CAGR is positive and max drawdown is -20%
- **THEN** Calmar SHALL be `CAGR / 0.20`

### Requirement: full_summary includes monthly returns and best/worst month

`_SingleResult.full_summary()` SHALL include best month (highest monthly return), worst month (lowest monthly return), and win rate (percentage of months with positive returns).

#### Scenario: Multi-year backtest
- **WHEN** `full_summary()` is called on a 5-year backtest
- **THEN** best_month, worst_month, and win_rate SHALL be computed from monthly resampled returns

### Requirement: BacktestResult.full_summary produces side-by-side comparison

`BacktestResult.full_summary()` SHALL return a DataFrame with each backtest as a column and all full metrics as rows, enabling easy comparison.

#### Scenario: Two backtests compared
- **WHEN** `result.full_summary()` is called on a BacktestResult with 2 backtests
- **THEN** a DataFrame with 2 columns (one per backtest) SHALL be returned
