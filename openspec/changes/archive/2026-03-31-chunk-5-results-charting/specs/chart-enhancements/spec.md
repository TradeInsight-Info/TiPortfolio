## ADDED Requirements

### Requirement: plot_security_weights shows weight evolution

`_SingleResult.plot_security_weights()` SHALL render a stacked area chart showing each asset's portfolio weight over time across rebalance dates. Requires trade records to compute weights at each rebalance.

#### Scenario: Monthly rebalance with 3 assets
- **WHEN** `result[0].plot_security_weights()` is called
- **THEN** a matplotlib Figure with a stacked area chart SHALL be returned, showing weight per asset at each rebalance date

### Requirement: plot_histogram shows return distribution

`_SingleResult.plot_histogram()` SHALL render a histogram of daily returns from the equity curve.

#### Scenario: Standard distribution plot
- **WHEN** `result[0].plot_histogram()` is called
- **THEN** a matplotlib Figure with a histogram of daily returns SHALL be returned

### Requirement: plot(interactive=True) renders with Plotly

When `plot(interactive=True)` is called, the equity curve SHALL be rendered using Plotly instead of Matplotlib. If Plotly is not installed, SHALL raise `ImportError` with a clear message.

#### Scenario: Interactive plot with Plotly installed
- **WHEN** `result[0].plot(interactive=True)` is called and plotly is available
- **THEN** a Plotly Figure object SHALL be returned

#### Scenario: Interactive plot without Plotly
- **WHEN** `plot(interactive=True)` is called and plotly is not installed
- **THEN** an `ImportError` SHALL be raised with message suggesting `pip install plotly`

### Requirement: BacktestResult chart methods delegate correctly

`BacktestResult.plot_security_weights()` and `BacktestResult.plot_histogram()` SHALL work for both single and multi-backtest results.

#### Scenario: Single backtest delegates
- **WHEN** `result.plot_histogram()` is called on a single-backtest result
- **THEN** it SHALL delegate to the inner `_SingleResult.plot_histogram()`

#### Scenario: Multi-backtest overlays
- **WHEN** `result.plot_histogram()` is called on a multi-backtest result
- **THEN** histograms for all backtests SHALL be overlaid on a single figure

### Requirement: Example script for full results and charting

The project SHALL include `examples/17_full_results.py` demonstrating `full_summary()`, `trades`, `trades.sample()`, `plot_security_weights()`, and `plot_histogram()` on a single backtest using offline CSV data.

#### Scenario: Single-backtest results example runs offline
- **WHEN** `examples/17_full_results.py` is executed with CSV files present
- **THEN** the script SHALL print `full_summary()`, print `trades.sample(3)`, and save charts

### Requirement: Example script for multi-backtest comparison

The project SHALL include `examples/18_multi_backtest_comparison.py` demonstrating `ti.run(bt1, bt2)` with side-by-side `summary()`, `full_summary()`, and overlaid `plot()` for two strategies using offline CSV data.

#### Scenario: Multi-backtest comparison example runs offline
- **WHEN** `examples/18_multi_backtest_comparison.py` is executed with CSV files present
- **THEN** the script SHALL print side-by-side comparison tables and save an overlaid equity curve chart
