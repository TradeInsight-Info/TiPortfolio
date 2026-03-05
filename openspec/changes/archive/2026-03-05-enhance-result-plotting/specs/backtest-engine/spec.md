## MODIFIED Requirements

### Requirement: plot_portfolio_beta auto-fetches benchmark

`plot_portfolio_beta()` SHALL accept optional `benchmark_symbol` and `benchmark_prices` parameters. If `benchmark_prices` is None, it SHALL fetch the benchmark data from YFinance using the symbol.

#### Scenario: auto-fetch when benchmark_prices not provided
- **WHEN** `result.plot_portfolio_beta()` is called without benchmark_prices
- **THEN** SPY data is fetched from YFinance automatically

#### Scenario: use provided benchmark_prices
- **WHEN** `result.plot_portfolio_beta(benchmark_prices=spy_df)` is called
- **THEN** the provided DataFrame is used

#### Scenario: custom benchmark symbol
- **WHEN** `result.plot_portfolio_beta(benchmark_symbol="QQQ")` is called
- **THEN** QQQ data is fetched from YFinance
