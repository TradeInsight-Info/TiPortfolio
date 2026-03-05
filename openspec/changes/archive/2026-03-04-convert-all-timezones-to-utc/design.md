## Context

The current TiPortfolio library handles price data with datetime indices that may come from various sources with different timezones. The `normalize_price_index` function currently converts all datetime indices to America/New_York timezone to ensure consistency for backtesting operations. However, New York timezone observes Daylight Saving Time (DST), which creates complications:

- Datetime conversions may shift hours unexpectedly during DST transitions
- Historical data spanning DST changes can have inconsistent local times
- Testing and debugging timezone-related issues is complex

The proposal suggests converting all data to UTC instead, which is DST-free and provides a universal reference point.

## Goals / Non-Goals

**Goals:**
- Eliminate DST-related issues by standardizing on UTC timezone
- Simplify datetime handling across the codebase
- Maintain consistent behavior for all historical data periods
- Ensure backtesting results are reproducible regardless of local timezone

**Non-Goals:**
- Change the external API interfaces (data input formats remain the same)
- Add timezone conversion options (always convert to UTC)
- Modify existing data storage formats
- Support multiple target timezones

## Decisions

**Timezone Target: UTC**
- **Decision**: Change `normalize_price_index` default timezone from 'America/New_York' to 'UTC'
- **Rationale**: UTC is the universal standard, DST-free, and simplifies global datetime operations. Unlike NY timezone, UTC provides consistent hour offsets year-round.
- **Alternatives Considered**:
  - Keep NY timezone but add DST-aware logic: Too complex, error-prone
  - Use local timezone: Inconsistent across different deployment environments
  - Allow configurable target timezone: Overcomplicates the API for minimal benefit

**Index Normalization Scope**
- **Decision**: Preserve existing normalization logic (convert naive to target tz, convert existing tz to target tz) but change target to UTC
- **Rationale**: Maintains backward compatibility in behavior while changing the target timezone
- **Alternatives Considered**:
  - Remove normalization entirely: Would break existing assumptions about consistent time references
  - Only normalize if naive: Could leave mixed timezone data

**Test Updates**
- **Decision**: Update test assertions and expected data to reflect UTC conversions
- **Rationale**: Tests must validate the new UTC behavior, not the old NY behavior
- **Alternatives Considered**:
  - Keep tests in NY timezone: Would defeat the purpose of UTC conversion

## Risks / Trade-offs

**Breaking Changes for Internal Code**
- Risk: Existing code expecting NY timezone may fail
- Mitigation: Update all internal usage systematically, run full test suite

**Historical Data Consistency**
- Risk: Backtest results may differ slightly due to timezone conversion differences
- Mitigation: Regenerate expected test results, document the change

**Performance Impact**
- Risk: UTC conversion adds minor computational overhead
- Mitigation: Negligible impact since conversion happens once per data load

**Migration Plan**

1. Update `normalize_price_index` function to use UTC as default
2. Update all call sites to use UTC instead of NY
3. Update test data loading and assertions
4. Run full test suite and regenerate expected results
5. Update documentation if needed
6. Rollback: Revert timezone parameter back to 'America/New_York'

**Open Questions**

None identified - the change is straightforward timezone parameter update.
