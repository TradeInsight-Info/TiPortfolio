## Why

The current system converts all price data to New York timezone for consistency, but New York observes Daylight Saving Time (DST), which introduces complexity and potential edge cases in datetime handling. Converting all data to UTC instead provides a simpler, DST-free timezone that ensures consistent behavior across all dates and avoids timezone conversion issues.

## What Changes

- **BREAKING**: Update `normalize_price_index` to convert all datetime indices to UTC instead of America/New_York timezone
- Update all timezone-related code in data loading, engine runs, and tests to use UTC as the target timezone
- Remove DST-related complexity by eliminating New York timezone conversions
- Ensure all datetime operations are performed in UTC for consistent results

## Capabilities

### New Capabilities
- `utc-timezone-normalization`: Standardize all datetime handling to UTC timezone for consistent, DST-free operations

### Modified Capabilities
- `backtest-engine`: Update timezone normalization to use UTC instead of NY timezone

## Impact

- `normalize_price_index` function in `calendar.py`
- `BacktestEngine.run` method and related timezone handling
- Data loading functions in `data.py`
- Test assertions and expected results that depend on timezone conversions
- No external dependencies affected, but internal datetime handling becomes more predictable
