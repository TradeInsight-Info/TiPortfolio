## ADDED Requirements

### Requirement: Quick start example
The system SHALL provide `examples/01_quick_start.py` that demonstrates monthly equal-weight rebalancing of QQQ, BIL, GLD — the Quick Example from api/index.md.

#### Scenario: Script runs and prints summary
- **WHEN** `uv run python examples/01_quick_start.py` is executed
- **THEN** the script prints a summary table and saves an equity curve PNG

### Requirement: Custom config example
The system SHALL provide `examples/02_custom_config.py` that demonstrates customising TiConfig (higher fees, different initial capital) and comparing the impact on returns.

#### Scenario: Script shows fee impact
- **WHEN** the script runs two backtests with different fee_per_share values
- **THEN** both summaries are printed showing the performance difference

### Requirement: Bond-equity split example
The system SHALL provide `examples/03_two_asset_bond_equity.py` that demonstrates a classic bond+equity equal-weight portfolio (e.g., TLT + SPY).

#### Scenario: Two-asset backtest
- **WHEN** the script runs with two tickers (one bond, one equity ETF)
- **THEN** summary and plot are produced showing the blended performance

### Requirement: Single asset example
The system SHALL provide `examples/04_single_asset.py` that demonstrates a single-ticker portfolio — effectively buy-and-hold with monthly rebalance.

#### Scenario: Single ticker backtest
- **WHEN** the script runs with one ticker
- **THEN** summary shows the ticker's own performance (minus fees)

### Requirement: Debug with PrintInfo example
The system SHALL provide `examples/05_debug_with_printinfo.py` that demonstrates using Action.PrintInfo to trace algo execution on each rebalance date.

#### Scenario: Debug output visible
- **WHEN** the script runs
- **THEN** console output shows `[date] portfolio=... selected=... weights=...` for each rebalance
