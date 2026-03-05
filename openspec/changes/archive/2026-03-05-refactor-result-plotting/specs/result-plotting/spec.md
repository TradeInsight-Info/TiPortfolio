# Purpose

Add visualization methods directly to BacktestResult class for more intuitive API.

## ADDED Requirements

### Requirement: BacktestResult.plot_portfolio() method

`BacktestResult` SHALL have a `plot_portfolio()` method that returns an interactive Plotly figure showing the equity curve and per-asset performance.

Constructor/Method parameters:
- `mark_rebalances: bool = True` — whether to show buy/sell markers on rebalance dates

#### Scenario: plot_portfolio returns Plotly figure
- **WHEN** `result.plot_portfolio()` is called
- **THEN** a Plotly Figure object is returned

#### Scenario: equity curve displayed as main line
- **WHEN** `result.plot_portfolio()` is called
- **THEN** the equity curve is displayed as the primary line in the chart

#### Scenario: rebalance markers shown when enabled
- **WHEN** `mark_rebalances=True` and result has rebalance decisions
- **THEN** buy/sell markers are shown on the chart at rebalance dates

#### Scenario: asset curves displayed when available
- **WHEN** result has asset_curves data
- **THEN** each asset's value over time is displayed as a line

---

### Requirement: BacktestResult.plot_rolling_book_composition() method

`BacktestResult` SHALL have a `plot_rolling_book_composition()` method for visualizing long/short book changes over time.

Method parameters:
- `book_column: str` — column name in asset_curves representing the book to visualize (e.g., "long", "short")

#### Scenario: returns Plotly figure
- **WHEN** `result.plot_rolling_book_composition(book_column="long")` is called
- **THEN** a Plotly Figure is returned

#### Scenario: heatmap shows asset presence in book over time
- **WHEN** method is called with valid book_column
- **THEN** a heatmap or similar visualization shows which assets were in the book at each rebalance date

#### Scenario: raises KeyError for invalid column
- **WHEN** `book_column` does not exist in asset_curves
- **THEN** KeyError is raised

---

### Requirement: BacktestResult.plot_portfolio_beta() method

`BacktestResult` SHALL have a `plot_portfolio_beta()` method for visualizing portfolio beta over time.

Method parameters:
- `benchmark_prices: pd.DataFrame` — benchmark price data for beta computation
- `lookback_days: int = 60` — rolling window for beta calculation

#### Scenario: returns Plotly figure
- **WHEN** `result.plot_portfolio_beta(benchmark_prices=spy_df)` is called
- **THEN** a Plotly Figure is returned

#### Scenario: displays rolling beta over time
- **WHEN** method is called with valid benchmark data
- **THEN** the chart shows portfolio beta computed over the lookback period

#### Scenario: handles missing benchmark data gracefully
- **WHEN** benchmark_prices is None or empty
- **THEN** an appropriate error message is raised

---

### Requirement: Standalone functions marked as deprecated

The standalone functions in `tiportfolio.report` SHALL show a deprecation warning when called.

#### Scenario: deprecated function shows warning
- **WHEN** `plot_portfolio_with_assets_interactive(result)` is called
- **THEN** a DeprecationWarning is raised suggesting to use `result.plot_portfolio()` instead
