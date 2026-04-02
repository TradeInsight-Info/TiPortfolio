# Spec: start-of-month-notebook

## Purpose

Demonstrates the simplest TiPortfolio strategy: a fixed ratio portfolio rebalanced monthly using `Weigh.Ratio` and `Signal.Monthly`.

## Requirements

### Requirement: Fixed ratio monthly rebalance notebook
The notebook SHALL demonstrate the simplest TiPortfolio strategy: a fixed 70% QQQ / 20% BIL / 10% GLD portfolio rebalanced monthly using `Weigh.Ratio` and `Signal.Monthly`.

#### Scenario: Data loading with offline CSV
- **WHEN** the notebook is run
- **THEN** data SHALL be loaded via `ti.fetch_data()` with `csv=CSV_DATA` for offline reproducibility

#### Scenario: Primary strategy construction
- **WHEN** building the main portfolio
- **THEN** the algo stack SHALL use `Signal.Monthly()`, `Select.All()`, `Weigh.Ratio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1})`, `Action.Rebalance()`

#### Scenario: Baseline comparison — QQQ only
- **WHEN** comparing strategies
- **THEN** the notebook SHALL include a 100% QQQ buy-and-hold baseline using `Signal.Once()`

#### Scenario: Baseline comparison — never rebalanced
- **WHEN** comparing strategies
- **THEN** the notebook SHALL include a same-allocation portfolio using `Signal.Once()` (buy initial weights, never rebalance)

#### Scenario: Multi-backtest comparison
- **WHEN** running all strategies
- **THEN** `ti.run(bt1, bt2, bt3)` SHALL produce side-by-side `summary()` and overlaid `plot()`

#### Scenario: Results exploration
- **WHEN** displaying results
- **THEN** the notebook SHALL show `full_summary()`, `trades.sample()`, `plot_security_weights()`, and `plot_histogram()`
