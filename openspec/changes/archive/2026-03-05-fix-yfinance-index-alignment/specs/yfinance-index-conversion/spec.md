# YFinance Index Conversion

## ADDED Requirements

### Requirement: YFinance data SHALL have DatetimeIndex after being fetched
YFinance.query() returns data with a RangeIndex and a separate 'date' column. The plot_portfolio_beta() method SHALL ensure the returned DataFrame is converted to have a proper DatetimeIndex before performing index alignment operations.

#### Scenario: RangeIndex is converted to DatetimeIndex
- **WHEN** YFinance.query() returns data with RangeIndex and 'date' column
- **THEN** the date column is set as index
- **AND** the resulting index is converted to DatetimeIndex (not RangeIndex)
- **AND** subsequent index alignment operations can match dates correctly

#### Scenario: DatetimeIndex conversion handles missing date column
- **WHEN** YFinance returns data without 'date' or 'Date' column
- **THEN** the method raises a clear error message
- **AND** the error indicates that benchmark data format is unexpected

#### Scenario: Timezone consistency is maintained
- **WHEN** DatetimeIndex is created from YFinance data
- **THEN** the index timezone matches the asset_curves timezone
- **OR** both are converted to tz-naive for alignment

### Requirement: Index alignment SHALL succeed when asset_curves and benchmark have overlapping dates
After proper DatetimeIndex conversion, the reindex() operation SHALL find overlapping dates between asset_curves and benchmark data, even if both come from different sources (one from backtest, one from YFinance).

#### Scenario: Overlapping dates are correctly identified after reindex
- **WHEN** asset_curves spans 2023-01-01 to 2023-12-31 (250+ trading days)
- **AND** benchmark data is fetched for the same date range from YFinance
- **THEN** after reindex(asset_curves.index), the benchmark DataFrame contains matching values (not all NaN)
- **AND** valid_idx = benchmark_aligned.dropna().index has length > 0

#### Scenario: Error handling when dates don't overlap
- **WHEN** benchmark data has been fetched but with a completely different date range
- **THEN** the method raises ValueError with clear message: "Not enough overlapping dates..."
- **AND** the message indicates the actual number of overlapping dates found
