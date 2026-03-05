# BacktestResult Plotting

## ADDED Requirements

### Requirement: BacktestResult SHALL be the canonical source for all portfolio plotting
All charting functionality related to BacktestResult instances SHALL be provided via methods on the BacktestResult class, not external functions in report.py.

#### Scenario: User plots portfolio equity curve via BacktestResult method
- **WHEN** user calls `result.plot_portfolio()`
- **THEN** method returns a Plotly chart of equity curve over time (existing functionality)

#### Scenario: User plots portfolio beta via BacktestResult method
- **WHEN** user calls `result.plot_portfolio_beta()`
- **THEN** method returns a Plotly chart of rolling portfolio beta (new functionality, spec'd separately)

#### Scenario: User plots book composition via BacktestResult method
- **WHEN** user calls `result.plot_rolling_book_composition(book_column)`
- **THEN** method returns a Plotly chart of book composition over rebalance dates (new functionality, spec'd separately)

### Requirement: Deprecated plotting functions in report.py SHALL be removed or marked obsolete
Functions `plot_equity_curve()` and `plot_portfolio_with_assets()` in report.py are legacy matplotlib-based functions that duplicate or conflict with BacktestResult Plotly methods.

#### Scenario: plot_equity_curve is unused outside tests
- **WHEN** codebase audit confirms plot_equity_curve() is only called in test files
- **THEN** function is removed from report.py entirely; test calls are updated to use BacktestResult.plot_portfolio()

#### Scenario: plot_portfolio_with_assets is unused outside tests
- **WHEN** codebase audit confirms plot_portfolio_with_assets() is only called in test files
- **THEN** function is removed from report.py; test calls are updated to equivalent BacktestResult methods

#### Scenario: Function is used in user notebooks
- **WHEN** external audit or user report indicates deprecated function is in use
- **THEN** function remains but is marked deprecated with warning message: "plot_equity_curve is deprecated. Use BacktestResult.plot_portfolio() instead."

### Requirement: All plotting methods SHALL return Plotly figures for consistency
Whether plotting from BacktestResult or report.py, all interactive charting functions SHALL return plotly.graph_objects.Figure objects (not matplotlib axes).

#### Scenario: BacktestResult method returns Plotly figure
- **WHEN** user calls `result.plot_portfolio()`, `result.plot_portfolio_beta()`, or `result.plot_rolling_book_composition()`
- **THEN** each returns a go.Figure object that can be displayed, saved, or further customized

#### Scenario: Plotly not installed error handling
- **WHEN** user calls a BacktestResult plotting method without plotly installed
- **THEN** method raises ImportError with message: "Plotly is required for interactive charts. Install with: uv add --dev plotly"

### Requirement: Notebook compatibility SHALL be verified
All BacktestResult plotting methods SHALL work correctly in Jupyter notebooks without requiring additional configuration.

#### Scenario: User calls plot method in Jupyter cell
- **WHEN** user runs `result.plot_portfolio_beta()` in a Jupyter notebook cell
- **THEN** Plotly chart is rendered inline without explicit `.show()` call

#### Scenario: User calls plot method in script
- **WHEN** user calls `result.plot_portfolio_beta()` in a standalone Python script
- **THEN** method returns figure object; user can display with fig.show() or save with fig.write_html()

#### Scenario: Multiple plots in same notebook
- **WHEN** user calls multiple plotting methods in sequence (plot_portfolio(), plot_portfolio_beta(), plot_rolling_book_composition())
- **THEN** each chart renders independently without interference

### Requirement: Report.py comparison functions SHALL remain unchanged
Functions `compare_strategies()`, `plot_strategy_comparison_interactive()`, and `rebalance_decisions_table()` are comparison utilities and shall NOT be affected by this change.

#### Scenario: compare_strategies still works
- **WHEN** user calls `report.compare_strategies(result1, result2, names=['A', 'B'])`
- **THEN** function returns metrics comparison table as before (no changes required)

#### Scenario: plot_strategy_comparison_interactive still works
- **WHEN** user calls `report.plot_strategy_comparison_interactive(result1, result2, ...)`
- **THEN** function returns Plotly figure comparing equity curves as before
