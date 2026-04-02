# Spec: vix-regime-notebook

## Purpose

Demonstrates a VIX regime-switching strategy using `Signal.VIX` with a parent/child portfolio tree that toggles between risk-on and risk-off allocations.

## Requirements

### Requirement: VIX regime switching notebook
The notebook SHALL demonstrate a VIX regime-switching strategy using `Signal.VIX` with a parent/child portfolio tree that toggles between risk-on and risk-off allocations.

#### Scenario: VIX data loading
- **WHEN** loading VIX data
- **THEN** VIX data SHALL be loaded from local CSV via `ti.fetch_data(["^VIX"], csv=CSV_DATA)`

#### Scenario: Child portfolio — low volatility regime
- **WHEN** VIX is below the low threshold
- **THEN** the low_vol child portfolio SHALL use `Weigh.Ratio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1})` (risk-on)

#### Scenario: Child portfolio — high volatility regime
- **WHEN** VIX is above the high threshold
- **THEN** the high_vol child portfolio SHALL use `Weigh.Ratio(weights={"QQQ": 0.4, "BIL": 0.4, "GLD": 0.2})` (risk-off)

#### Scenario: Parent portfolio with VIX signal
- **WHEN** building the parent portfolio
- **THEN** it SHALL use `Signal.Monthly()`, `Signal.VIX(high=30, low=20, data=vix_data)`, `Action.Rebalance()` with `[low_vol, high_vol]` as children

#### Scenario: Baseline comparisons
- **WHEN** comparing strategies
- **THEN** the notebook SHALL include QQQ-only and fixed 70/20/10 monthly baselines

#### Scenario: Multi-backtest comparison
- **WHEN** comparing all strategies
- **THEN** `ti.run()` SHALL produce side-by-side `summary()` and overlaid `plot()`
