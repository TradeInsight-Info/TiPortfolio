## 1. Implement plot_portfolio method

- [x] 1.1 Extract plotting logic from report.py plot_portfolio_with_assets_interactive to backtest.py
- [x] 1.2 Add plot_portfolio() method to BacktestResult class
- [x] 1.3 Add mark_rebalances parameter support
- [x] 1.4 Test plot_portfolio() returns Plotly figure

## 2. Implement plot_rolling_book_composition method

- [x] 2.1 Add plot_rolling_book_composition() method to BacktestResult
- [x] 2.2 Implement heatmap visualization for book composition over time
- [x] 2.3 Add KeyError handling for invalid book_column
- [x] 2.4 Test visualization 3. Implement renders correctly

## plot_portfolio_beta method

- [x] 3.1 Add plot_portfolio_beta() method to BacktestResult
- [x] 3.2 Implement rolling beta computation with benchmark_prices
- [x] 3.3 Add lookback_days parameter (default 60)
- [x] 3.4 Handle missing benchmark data gracefully

## 4. Add deprecation warnings

- [x] 4.1 Add DeprecationWarning to plot_portfolio_with_assets_interactive in report.py
- [x] 4.2 Update docstrings to indicate deprecation

## 5. Update exports and documentation

- [x] 5.1 Verify BacktestResult methods are accessible from tiportfolio import
- [x] 5.2 Run type checking (mypy)
- [x] 5.3 Run tests to ensure no regressions
