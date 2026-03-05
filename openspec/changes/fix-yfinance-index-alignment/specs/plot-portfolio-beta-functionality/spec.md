# Plot Portfolio Beta Functionality Fix

## MODIFIED Requirements

### Requirement: BacktestResult SHALL plot rolling portfolio beta when benchmark data is auto-fetched
BacktestResult.plot_portfolio_beta() SHALL work correctly when benchmark_prices is not provided, automatically fetching benchmark data from YFinance and ensuring proper index alignment before calculating rolling beta.

#### Scenario: Beta chart is generated when calling without benchmark_prices
- **WHEN** user calls result.plot_portfolio_beta() without passing benchmark_prices
- **AND** asset_curves contains 250+ dates spanning a full year
- **THEN** the method fetches SPY data from YFinance
- **AND** a valid Plotly figure is returned with rolling beta values
- **AND** no "Not enough overlapping dates" error is raised

#### Scenario: Cached benchmark data is reused on subsequent calls
- **WHEN** plot_portfolio_beta() is called twice without benchmark_prices
- **THEN** the second call uses _cached_benchmark from the first call
- **AND** YFinance is not queried again
- **AND** same figure is generated both times

#### Scenario: Explicit benchmark_prices still takes precedence
- **WHEN** user provides benchmark_prices as a DataFrame
- **THEN** the provided data is used
- **AND** YFinance is not queried
- **AND** caching mechanism is bypassed

#### Scenario: Clear error when benchmark data cannot be fetched
- **WHEN** YFinance query fails or returns empty data
- **THEN** method raises ValueError with message: "Could not fetch benchmark data for <symbol>"
- **AND** no partial data or NaN-filled charts are returned

### Requirement: Index alignment SHALL be robust across different timezone states
The fix SHALL handle timezone normalization correctly, ensuring that asset_curves (potentially tz-aware from backtest) and benchmark data (potentially tz-naive from YFinance) can be reliably aligned.

#### Scenario: tz-aware asset_curves aligns with tz-naive benchmark data
- **WHEN** asset_curves has tz-aware DatetimeIndex (e.g., UTC)
- **AND** benchmark data from YFinance is tz-naive
- **THEN** both are converted to tz-naive before reindex
- **AND** overlapping dates are correctly identified

#### Scenario: Both tz-naive indices align correctly
- **WHEN** both asset_curves and benchmark are tz-naive DatetimeIndex
- **THEN** reindex() matches dates directly
- **AND** no timezone conversion errors occur

#### Scenario: DatetimeIndex is ensured after fetch
- **WHEN** YFinance returns data with RangeIndex
- **THEN** after set_index('date') and pd.to_datetime(), the index type is DatetimeIndex
- **AND** isinstance(benchmark_data.index, pd.DatetimeIndex) returns True
