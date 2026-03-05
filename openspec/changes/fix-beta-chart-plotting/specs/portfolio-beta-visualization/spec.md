# Portfolio Beta Visualization

## ADDED Requirements

### Requirement: BacktestResult SHALL plot rolling portfolio beta against benchmark
The system SHALL provide `BacktestResult.plot_portfolio_beta()` method that computes rolling portfolio beta against a benchmark (default SPY) and returns an interactive Plotly chart.

#### Scenario: User provides benchmark prices
- **WHEN** user calls `result.plot_portfolio_beta(benchmark_prices=df)` with a DataFrame containing benchmark close prices
- **THEN** method uses the provided prices and returns a Plotly figure with rolling beta line chart

#### Scenario: System fetches benchmark from YFinance
- **WHEN** user calls `result.plot_portfolio_beta()` without providing benchmark_prices
- **THEN** system automatically fetches benchmark data (SPY by default) from YFinance for the asset_curves date range and returns the chart

#### Scenario: Insufficient overlapping dates error
- **WHEN** user calls `result.plot_portfolio_beta(lookback_days=60)` but asset_curves and benchmark have fewer than 61 overlapping dates
- **THEN** method raises ValueError with message: "Not enough overlapping dates. Need at least N, got M"

### Requirement: Timezone handling SHALL be robust across tz-naive and tz-aware indices
The method SHALL correctly align asset_curves and benchmark_prices indices regardless of timezone awareness state.

#### Scenario: Both indices are tz-aware (UTC)
- **WHEN** asset_curves has UTC timezone and benchmark_prices has UTC timezone
- **THEN** indices are aligned correctly and rolling beta is computed without errors

#### Scenario: Mixed timezone awareness (one tz-naive, one tz-aware)
- **WHEN** asset_curves is tz-naive and benchmark_prices is tz-aware (or vice versa)
- **THEN** method normalizes both to tz-naive UTC before alignment and returns correct beta

#### Scenario: Different timezones (e.g., US/Eastern vs UTC)
- **WHEN** asset_curves has timezone America/New_York and benchmark_prices has UTC
- **THEN** method converts both to tz-naive UTC and aligns correctly

### Requirement: Rolling beta calculation SHALL use OLS covariance-based beta
The method SHALL compute rolling portfolio beta as: β = Cov(portfolio_returns, benchmark_returns) / Var(benchmark_returns)

#### Scenario: Two-asset portfolio
- **WHEN** result has 2 assets (long/short pair) and lookback_days=60
- **THEN** method computes 60-day rolling portfolio beta (sum of (weight_i * beta_i)) and returns values for each date after the lookback window

#### Scenario: Multi-asset portfolio
- **WHEN** result has 5+ assets with varying returns and lookback_days=60
- **THEN** method computes portfolio beta correctly as weighted average of individual asset betas

### Requirement: Chart formatting SHALL display beta relative to benchmark
The returned Plotly figure SHALL include:
- Y-axis line at β=1.0 (dashed, gray, labeled "β=1")
- Y-axis line at β=0.0 (dashed, gray, labeled "β=0")
- Portfolio beta line (solid, width=2) with date on x-axis
- Hover template showing date and beta value (4 decimals)
- Title: "Rolling Portfolio Beta (lookback=N days)"

#### Scenario: Default chart formatting
- **WHEN** user calls `result.plot_portfolio_beta()` and method returns figure
- **THEN** figure includes both β=0 and β=1 reference lines, properly labeled and formatted

#### Scenario: Customizable lookback period
- **WHEN** user calls `result.plot_portfolio_beta(lookback_days=120)`
- **THEN** title shows "lookback=120 days" and rolling window is 120 days
