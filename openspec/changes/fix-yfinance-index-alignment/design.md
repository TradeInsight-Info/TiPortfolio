# Design: Fix YFinance Index Alignment

## Context

The `BacktestResult.plot_portfolio_beta()` method attempts to fetch benchmark data from YFinance when `benchmark_prices` is not provided. YFinance's `query()` method returns a DataFrame with:
- A numeric RangeIndex (0, 1, 2, ..., N-1) instead of a DatetimeIndex
- A separate 'date' column containing the actual trading dates
- OHLCV columns (open, high, low, close, volume) plus adjusted close

The current implementation attempts to set the 'date' column as the index, but does not explicitly convert the resulting index to DatetimeIndex. When the index remains as a generic object or RangeIndex, the subsequent `reindex(asset_curves.index)` operation fails to match dates, resulting in all NaN values. This causes the validation check to fail with "Not enough overlapping dates. Need at least 61, got 0".

## Goals / Non-Goals

**Goals:**
- Fix the YFinance data conversion to ensure DatetimeIndex is created
- Enable `plot_portfolio_beta()` to work without explicit benchmark_prices
- Maintain backward compatibility with explicitly provided benchmark_prices
- Handle timezone consistency between asset_curves and benchmark data
- Preserve the caching mechanism for repeated calls

**Non-Goals:**
- Change the YFinance data fetching strategy or parameters
- Modify how asset_curves are created or indexed
- Add new parameters to plot_portfolio_beta()
- Implement fallback benchmark sources other than YFinance

## Decisions

### Decision 1: Explicit DatetimeIndex Conversion
After setting the 'date' column as index using `set_index('date')`, explicitly convert the index using `pd.to_datetime()` to ensure it is a proper DatetimeIndex.

**Rationale:**
- `set_index()` creates an index but does not guarantee its type
- YFinance returns dates as strings, which become object dtype when set as index
- Explicit conversion ensures `isinstance(index, pd.DatetimeIndex)` is True
- Allows subsequent timezone handling logic to work correctly

**Implementation:**
```python
# After set_index('date')
if not isinstance(benchmark_data.index, pd.DatetimeIndex):
    benchmark_data.index = pd.to_datetime(benchmark_data.index)
```

### Decision 2: Timezone Normalization Before Reindex
Convert both asset_curves and benchmark_prices to tz-naive indices before performing reindex operations.

**Rationale:**
- asset_curves may have tz-aware indices (UTC from backtest)
- YFinance returns tz-naive dates
- Reindex fails when indices have different timezone awareness
- Converting both to tz-naive is safe because dates are preserved, only timezone info is lost
- This approach handles all combinations: tz-aware/tz-aware, tz-naive/tz-naive, mixed

**Implementation:**
```python
# Make copies and normalize both to tz-naive
asset_curves = self.asset_curves.copy()
benchmark_prices = benchmark_prices.copy()

try:
    if asset_curves.index.tz is not None:
        asset_curves.index = asset_curves.index.tz_localize(None)
except TypeError:
    pass  # Already tz-naive

try:
    if benchmark_prices.index.tz is not None:
        benchmark_prices.index = benchmark_prices.index.tz_localize(None)
except TypeError:
    pass  # Already tz-naive
```

### Decision 3: Robust Index Type Checking
Check whether the index is actually a DatetimeIndex rather than assuming `set_index()` produces one.

**Rationale:**
- Makes the fix explicit and testable
- Guards against future changes to YFinance return format
- Provides clear failure mode if date parsing fails

**Implementation:**
```python
if not isinstance(benchmark_data.index, pd.DatetimeIndex):
    benchmark_data.index = pd.to_datetime(benchmark_data.index)
```

## Risks / Trade-offs

### Risk 1: Different Date Ranges
If YFinance returns data for a different date range than asset_curves (e.g., market holidays, data gaps), the reindex will still produce NaN for non-overlapping dates. The validation check will correctly catch this.

**Mitigation:** Error message clearly indicates how many overlapping dates were found, helping users diagnose issues.

### Risk 2: Date Format Changes
If YFinance changes its return format (e.g., different column name for dates), the code will still fail at the set_index step, but with a more obvious error about missing 'date' column.

**Mitigation:** The code checks for both 'date' and 'Date' columns, providing some robustness. Future changes would be caught quickly by test failures.

### Risk 3: Performance
Making copies of DataFrames (asset_curves and benchmark_prices) for timezone conversion adds minor memory overhead.

**Mitigation:** Copies are only made during plot_portfolio_beta() calls, which are expensive operations already (fetching data, calculating rolling beta). The memory impact is negligible.

### Trade-off: Explicit vs Implicit Conversion
Chose explicit `pd.to_datetime()` conversion rather than relying on pandas auto-detection.

**Rationale:** Makes intention clear, ensures predictable behavior, easier to test and debug.
