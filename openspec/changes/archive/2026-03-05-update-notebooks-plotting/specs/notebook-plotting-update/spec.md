# Purpose

Update notebooks to use new BacktestResult plotting methods and add beta charts.

## ADDED Requirements

### Requirement: Notebooks use result.plot_portfolio()

All Jupyter notebooks SHALL use the new `result.plot_portfolio()` method instead of the deprecated `plot_portfolio_with_assets_interactive()` function.

#### Scenario: beta_neutral_dynamic.ipynb updated
- **WHEN** the notebook is opened
- **THEN** it uses `result.plot_portfolio()` for portfolio visualization

#### Scenario: dollar_neutral_txn_kvue.ipynb updated
- **WHEN** the notebook is opened
- **THEN** it uses `result.plot_portfolio()` for portfolio visualization

#### Scenario: volatility_targeting_qqq_bil_gld.ipynb updated
- **WHEN** the notebook is opened
- **THEN** it uses `result.plot_portfolio()` for portfolio visualization

#### Scenario: start_of_month_rebalance.ipynb updated
- **WHEN** the notebook is opened
- **THEN** it uses `result.plot_portfolio()` for portfolio visualization

#### Scenario: vix_target_rebalance.ipynb updated
- **WHEN** the notebook is opened
- **THEN** it uses `result.plot_portfolio()` for portfolio visualization

---

### Requirement: Long/short notebooks include beta chart

Notebooks that use long/short strategies SHALL include a beta chart using `result.plot_portfolio_beta()`.

#### Scenario: beta_neutral_dynamic.ipynb has beta chart
- **WHEN** the notebook is run
- **THEN** it displays a beta chart using `result.plot_portfolio_beta(spy_df)`

#### Scenario: dollar_neutral_txn_kvue.ipynb has beta chart
- **WHEN** the notebook is run
- **THEN** it displays a beta chart using `result.plot_portfolio_beta(spy_df)`

---

### Requirement: Notebooks execute without errors

All updated notebooks SHALL execute without errors.

#### Scenario: All notebooks run successfully
- **WHEN** each notebook is run in order
- **THEN** no execution errors occur
