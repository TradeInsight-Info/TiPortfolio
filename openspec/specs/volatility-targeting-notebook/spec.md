# Spec: volatility-targeting-notebook

## Purpose

Demonstrates inverse-volatility weighting using `Weigh.BasedOnHV` on QQQ/BIL/GLD with a quarterly rebalance schedule.

## Requirements

### Requirement: Volatility targeting notebook
The notebook SHALL demonstrate inverse-volatility weighting using `Weigh.BasedOnHV` on QQQ/BIL/GLD with a quarterly rebalance schedule.

#### Scenario: Primary strategy with BasedOnHV
- **WHEN** building the volatility-targeting portfolio
- **THEN** the algo stack SHALL use `Signal.Quarterly()`, `Select.All()`, `Weigh.BasedOnHV(initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}, target_hv=0.15, lookback=pd.DateOffset(months=1))`, `Action.Rebalance()`

#### Scenario: Weight evolution visualization
- **WHEN** the backtest completes
- **THEN** the notebook SHALL display weight evolution over time using `plot_security_weights()`

#### Scenario: Baseline comparison
- **WHEN** comparing strategies
- **THEN** the notebook SHALL include a fixed 70/20/10 ratio baseline and a QQQ-only baseline

#### Scenario: Target vol sensitivity
- **WHEN** exploring parameter sensitivity
- **THEN** the notebook SHALL re-run with a different `target_hv` value (e.g., 0.10) and compare results

#### Scenario: Multi-backtest comparison
- **WHEN** comparing all strategies
- **THEN** `ti.run()` SHALL produce side-by-side `summary()` and overlaid `plot()`
