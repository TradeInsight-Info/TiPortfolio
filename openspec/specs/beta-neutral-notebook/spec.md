# Spec: beta-neutral-notebook

## Purpose

Demonstrates a beta-neutral strategy using `Weigh.BasedOnBeta` that dynamically adjusts weights to maintain near-zero portfolio beta.

## Requirements

### Requirement: Beta-neutral dynamic notebook
The notebook SHALL demonstrate a beta-neutral strategy using `Weigh.BasedOnBeta(target_beta=0)` that dynamically adjusts weights to maintain near-zero portfolio beta.

#### Scenario: Universe and data loading
- **WHEN** setting up the strategy
- **THEN** the notebook SHALL use QQQ/BIL/GLD as traded tickers and AAPL as the beta reference (base_data), loaded via `ti.fetch_data()` with CSV

#### Scenario: Beta-neutral portfolio construction
- **WHEN** building the portfolio
- **THEN** the algo stack SHALL use `Signal.Monthly()`, `Select.All()`, `Weigh.BasedOnBeta(initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}, target_beta=0, lookback=pd.DateOffset(months=1), base_data=aapl_data)`, `Action.Rebalance()`

#### Scenario: Weight adaptation visualization
- **WHEN** the backtest completes
- **THEN** the notebook SHALL display how weights shift over time via `plot_security_weights()`

#### Scenario: Baseline comparisons
- **WHEN** comparing strategies
- **THEN** the notebook SHALL include equal-weight and QQQ-only baselines

#### Scenario: Multi-backtest comparison
- **WHEN** comparing all strategies
- **THEN** `ti.run()` SHALL produce side-by-side `summary()` and overlaid `plot()`

#### Scenario: Results exploration
- **WHEN** displaying detailed results
- **THEN** the notebook SHALL show `full_summary()` and `trades.sample()`
