# Spec: interactive-portfolio-chart

## Purpose

Provides an interactive Plotly-based chart for visualizing portfolio equity curves, per-asset breakdowns, trade markers, and drawdown subplots.

## Requirements

### Requirement: Per-asset equity curves
The `plot_interactive()` method SHALL render one line trace per asset showing its position value (qty × close price) over time, plus a bold total portfolio equity line.

#### Scenario: Multiple asset lines displayed
- **WHEN** `result[0].plot_interactive()` is called on a backtest with QQQ, BIL, GLD
- **THEN** the chart SHALL display 4 lines: one for QQQ value, one for BIL value, one for GLD value, and one bold line for total portfolio equity

#### Scenario: Asset value calculated from positions and prices
- **WHEN** rendering per-asset equity
- **THEN** for each trading day, the asset value SHALL equal `qty_held × close_price`, where `qty_held` is forward-filled from the most recent trade record for that ticker

#### Scenario: Asset with zero position
- **WHEN** a ticker has no position (qty = 0) on a given date
- **THEN** that ticker's value line SHALL show 0 for that date

### Requirement: Hover tooltips on equity lines
The chart SHALL show hover tooltips when the user hovers over any equity line.

#### Scenario: Hovering over asset line
- **WHEN** user hovers over a point on an asset line (e.g., QQQ)
- **THEN** the tooltip SHALL display: date and dollar value

#### Scenario: Hovering over total equity line
- **WHEN** user hovers over the total portfolio equity line
- **THEN** the tooltip SHALL display: date and total portfolio value

### Requirement: Buy trade markers
The chart SHALL display green upward triangle markers at buy trade points.

#### Scenario: Buy marker displayed
- **WHEN** a trade record has `delta > 0` (buy)
- **THEN** a green upward triangle marker SHALL be placed on that ticker's asset equity line at the trade date

#### Scenario: Buy marker vertical line
- **WHEN** a buy marker is displayed
- **THEN** a green dotted vertical line SHALL extend from x-axis to the marker

#### Scenario: Buy marker hover tooltip
- **WHEN** user hovers over a buy marker
- **THEN** the tooltip SHALL display: date, "BUY", ticker, price, quantity (delta)

### Requirement: Sell trade markers
The chart SHALL display red downward triangle markers at sell trade points.

#### Scenario: Sell marker displayed
- **WHEN** a trade record has `delta < 0` (sell)
- **THEN** a red downward triangle marker SHALL be placed on that ticker's asset equity line at the trade date

#### Scenario: Sell marker vertical line
- **WHEN** a sell marker is displayed
- **THEN** a red dotted vertical line SHALL extend from x-axis to the marker

#### Scenario: Sell marker hover tooltip
- **WHEN** user hovers over a sell marker
- **THEN** the tooltip SHALL display: date, "SELL", ticker, price, quantity (abs delta)

### Requirement: Drawdown subplot
The chart SHALL include a drawdown subplot below the equity chart.

#### Scenario: Single-backtest drawdown
- **WHEN** `result[0].plot_interactive()` is called
- **THEN** the chart SHALL display a filled area drawdown chart below the equity chart showing `(equity - cummax) / cummax`

#### Scenario: Multi-backtest drawdown
- **WHEN** `comparison.plot_interactive()` is called on a multi-backtest result
- **THEN** the drawdown subplot SHALL show one drawdown line per strategy, colour-matched to the equity lines

### Requirement: Multi-backtest comparison chart
`BacktestResult.plot_interactive()` SHALL support comparing multiple backtests in a single interactive chart.

#### Scenario: Multi-backtest overlaid equity curves
- **WHEN** `comparison.plot_interactive()` is called on a result from `ti.run(bt1, bt2, bt3)`
- **THEN** the chart SHALL display one total equity line per backtest strategy, each with a distinct colour and labelled by strategy name

#### Scenario: Multi-backtest trade markers per strategy
- **WHEN** `comparison.plot_interactive()` is called on a multi-backtest result
- **THEN** buy/sell trade markers SHALL be shown for each strategy, colour-coded to match the strategy's equity line, and togglable via legend

#### Scenario: Multi-backtest hover tooltips
- **WHEN** user hovers over any equity line in a multi-backtest chart
- **THEN** the tooltip SHALL display: strategy name, date, and total portfolio value

#### Scenario: Multi-backtest hover on trade marker
- **WHEN** user hovers over a trade marker in a multi-backtest chart
- **THEN** the tooltip SHALL display: strategy name, date, BUY/SELL, ticker, price, quantity

#### Scenario: Single result delegation
- **WHEN** `result.plot_interactive()` is called on a single-backtest result
- **THEN** it SHALL delegate to `_SingleResult.plot_interactive()` showing per-asset breakdown with trade markers

### Requirement: Interactive in notebook
The chart SHALL render interactively in Jupyter notebooks using Plotly.

#### Scenario: Notebook rendering
- **WHEN** `plot_interactive()` is called in a Jupyter notebook
- **THEN** the chart SHALL render as an interactive Plotly figure with zoom, pan, and hover

### Requirement: PNG export
The chart SHALL support saving as a static PNG image.

#### Scenario: Save as PNG via write_image
- **WHEN** user calls `fig = result[0].plot_interactive()` followed by `fig.write_image("chart.png")`
- **THEN** a static PNG file SHALL be saved at the specified path

#### Scenario: Existing plot() unchanged
- **WHEN** user calls `result.plot()`
- **THEN** the existing matplotlib behavior SHALL be unchanged (backwards compatible)

### Requirement: Prices data available on result
The `_SingleResult` SHALL have access to price data for per-asset value reconstruction.

#### Scenario: Prices stored on result
- **WHEN** a backtest completes
- **THEN** the `_SingleResult` SHALL have access to the price DataFrames used in the backtest
