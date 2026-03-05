## Context

We have added plotting methods to BacktestResult. Now we need to enhance them.

## Goals

1. Make plot_portfolio_beta() auto-fetch benchmark data
2. Clean up report.py - keep only essential functions
3. Update notebooks with beta charts

## Decisions

1. plot_portfolio_beta() default: benchmark_symbol="SPY", benchmark_prices=None → auto-fetch
2. report.py: Remove deprecated plot_portfolio_with_assets_interactive (already deprecated)
3. Notebooks: Use new method with auto-fetch
