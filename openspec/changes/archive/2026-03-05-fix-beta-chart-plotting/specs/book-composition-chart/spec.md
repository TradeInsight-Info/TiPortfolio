# Book Composition Chart

## ADDED Requirements

### Requirement: BacktestResult SHALL plot rolling long/short book composition over rebalance dates
The system SHALL provide `BacktestResult.plot_rolling_book_composition(book_column)` method that visualizes the composition (which assets are active) in a specified long or short book over all rebalance dates.

#### Scenario: User specifies a long book column
- **WHEN** user calls `result.plot_rolling_book_composition("long_book")` and asset_curves contains a "long_book" column
- **THEN** method returns a Plotly heatmap showing which assets had non-zero positions in that book at each rebalance date

#### Scenario: User specifies a short book column
- **WHEN** user calls `result.plot_rolling_book_composition("short_book")`
- **THEN** method returns a Plotly heatmap showing short book composition over rebalance dates

#### Scenario: Column does not exist in asset_curves
- **WHEN** user calls `result.plot_rolling_book_composition("nonexistent_column")`
- **THEN** method raises KeyError with message: "Column 'nonexistent_column' not found in asset_curves"

#### Scenario: No rebalance decisions exist
- **WHEN** result.rebalance_decisions is empty
- **THEN** method uses all dates from asset_curves index as reference dates (not just rebalance dates)

### Requirement: Heatmap cells SHALL indicate asset presence in book
The heatmap SHALL use a binary color scheme:
- **1 (colored)**: Asset had non-zero position (value > 0) in that book at the date
- **0 (uncolored)**: Asset had zero or negative position in that book at the date

#### Scenario: Asset enters and exits book
- **WHEN** asset ABC appears in long_book from 2023-01-15 to 2023-03-30, then disappears
- **THEN** heatmap shows colored cell (1) for ABC rows at those dates, and uncolored cells (0) before and after

#### Scenario: Multiple assets in book at same date
- **WHEN** long_book at 2023-02-01 contains assets [ABC: $5000, DEF: $3000, GHI: $2000] (all > 0)
- **THEN** heatmap row for that date shows 1 for ABC, DEF, GHI columns and 0 for others

### Requirement: Heatmap formatting SHALL be clear and labeled
The returned Plotly figure SHALL include:
- **X-axis**: Rebalance dates (or asset_curves dates if no rebalances), formatted as YYYY-MM-DD
- **Y-axis**: Asset names, sorted alphabetically
- **Color scale**: Blues (colorscale='Blues'), with showscale=False
- **Title**: "Rolling Book Composition: {book_column}"
- **Hover**: Clicking cells shows date and asset name

#### Scenario: Default heatmap appearance
- **WHEN** user calls `result.plot_rolling_book_composition("long_book")` and method returns figure
- **THEN** figure has proper axis labels, sorted asset list, and "Rolling Book Composition: long_book" title

#### Scenario: No assets in book at any date
- **WHEN** book_column contains all zeros across all dates
- **THEN** method raises ValueError with message: "No assets found in book column"

### Requirement: Asset list SHALL be extracted from non-zero positions
The heatmap shall automatically discover which assets appear in the book (not require manual specification).

#### Scenario: Assets dynamically added and removed
- **WHEN** rebalance_decisions show assets being added and removed at different dates
- **THEN** y-axis shows all assets that appear in the book at any point, sorted alphabetically, even if not present in all rebalances

#### Scenario: Asset present only at start
- **WHEN** asset XYZ is in the book only at the first rebalance date, then never appears again
- **THEN** asset XYZ row is included in the heatmap with a single colored cell, zeros elsewhere
