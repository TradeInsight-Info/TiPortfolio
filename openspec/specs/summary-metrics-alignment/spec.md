## ADDED Requirements

### Requirement: summary() returns all documented metrics

`_SingleResult.summary()` SHALL return a DataFrame containing all metrics documented in `docs/api/index.md` summary table, in this order: `risk_free_rate`, `total_return`, `cagr`, `sharpe`, `sortino`, `max_drawdown`, `calmar`, `kelly`, `final_value`, `total_fee`, `rebalance_count`.

#### Scenario: summary contains Sortino ratio
- **WHEN** `result[0].summary()` is called
- **THEN** the DataFrame SHALL contain a `sortino` row

#### Scenario: summary contains Kelly leverage
- **WHEN** `result[0].summary()` is called
- **THEN** the DataFrame SHALL contain a `kelly` row computed as `mean_excess_return / variance_of_excess_returns`

#### Scenario: summary contains final_value
- **WHEN** `result[0].summary()` is called
- **THEN** the DataFrame SHALL contain a `final_value` row equal to the last equity curve value

#### Scenario: summary contains total_fee and rebalance_count
- **WHEN** `result[0].summary()` is called on a backtest with trade records
- **THEN** `total_fee` SHALL equal the sum of all trade record fees, and `rebalance_count` SHALL equal the number of distinct rebalance dates

### Requirement: _run_single tracks total fees and rebalance count

`_run_single` SHALL compute `total_fee` (sum of all trade record fees) and `rebalance_count` (number of distinct rebalance dates) from accumulated trade records and pass them to `_SingleResult`.

#### Scenario: Fee tracking across rebalances
- **WHEN** a backtest completes with multiple rebalance events
- **THEN** `total_fee` SHALL be the sum of the `fee` column across all trade records

### Requirement: Example 02 uses multi-backtest API

`examples/02_custom_config.py` SHALL use `ti.run(bt_low, bt_high, bt_big)` to run all three backtests in one call and print side-by-side comparison via `result.summary()`.

#### Scenario: Side-by-side output
- **WHEN** example 02 is run
- **THEN** it SHALL print a single DataFrame with columns for each portfolio name
