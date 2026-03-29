## ADDED Requirements

### Requirement: _SingleResult holds one backtest's results
The system SHALL provide `_SingleResult` that stores the portfolio name, equity curve (list of (date, equity) tuples or pd.Series), and a reference to TiConfig.

#### Scenario: Access equity curve
- **WHEN** a backtest completes and produces a _SingleResult
- **THEN** the equity curve is accessible as a pd.Series with DatetimeIndex

### Requirement: BacktestResult is always a collection
The system SHALL provide `BacktestResult` that wraps `list[_SingleResult]`. It SHALL support `result[0]` (int index) and `result["name"]` (string index by portfolio name).

#### Scenario: Single backtest indexing
- **WHEN** `ti.run(backtest)` returns a BacktestResult with one result named "monthly"
- **THEN** `result[0]` and `result["monthly"]` both return the same _SingleResult

#### Scenario: Invalid index raises error
- **WHEN** `result["nonexistent"]` is accessed
- **THEN** `KeyError` is raised

### Requirement: summary() returns a DataFrame of key metrics
The system SHALL provide `summary()` on `_SingleResult` that returns a `pd.DataFrame` with at minimum: total return, CAGR, max drawdown, Sharpe ratio.

#### Scenario: Summary after backtest
- **WHEN** `result[0].summary()` is called after a completed backtest
- **THEN** a DataFrame is returned with rows for total_return, cagr, max_drawdown, sharpe

#### Scenario: Sharpe uses config.risk_free_rate
- **WHEN** summary is computed with `risk_free_rate=0.04` and `bars_per_year=252`
- **THEN** the Sharpe ratio is `(annualised_return - 0.04) / annualised_volatility`

### Requirement: plot() renders a static Matplotlib chart
The system SHALL provide `plot()` on `_SingleResult` that renders an equity curve chart using Matplotlib. It SHALL also render a drawdown subplot below the equity curve.

#### Scenario: Plot produces a figure
- **WHEN** `result[0].plot()` is called
- **THEN** a Matplotlib figure is created with equity curve and drawdown subplots

### Requirement: BacktestResult delegates summary and plot
The system SHALL provide `summary()` and `plot()` on `BacktestResult` that delegate to the underlying `_SingleResult`(s).

#### Scenario: BacktestResult.summary with single result
- **WHEN** `result.summary()` is called on a BacktestResult with one result
- **THEN** it returns the same DataFrame as `result[0].summary()`
