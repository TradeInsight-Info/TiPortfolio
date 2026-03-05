## MODIFIED Requirements

### Requirement: BacktestResult summary output
`BacktestResult.summary()` SHALL return a human-readable string that includes `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, `kelly_leverage`, `mean_excess_return`, `final_value`, `total_fee`, and rebalance count, in that display order.

#### Scenario: Summary includes Sortino ratio
- **WHEN** `result.summary()` is called on a completed backtest
- **THEN** the returned string contains a line with "Sortino Ratio:" and a numeric value

#### Scenario: Summary includes mean excess return
- **WHEN** `result.summary()` is called on a completed backtest
- **THEN** the returned string contains a line with "Mean Excess Return:" and a numeric value

#### Scenario: Summary metric order
- **WHEN** `result.summary()` is called
- **THEN** Sharpe Ratio appears before Sortino Ratio, which appears before MAR Ratio, which appears before CAGR, which appears before Max Drawdown

## MODIFIED Requirements

### Requirement: compare_strategies top-5 metrics
`compare_strategies()` SHALL compare strategies on exactly 5 metrics: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, in that order. `sortino_ratio` is higher-is-better.

#### Scenario: Comparison DataFrame has exactly 5 rows
- **WHEN** `compare_strategies()` is called with two or more BacktestResult instances
- **THEN** the returned DataFrame has exactly 5 rows with index `["sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown"]`

#### Scenario: Sortino ratio comparison direction
- **WHEN** one strategy has a higher `sortino_ratio` than others
- **THEN** that strategy is identified as "better" in the `sortino_ratio` row
