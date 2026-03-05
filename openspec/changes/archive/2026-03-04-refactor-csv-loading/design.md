## Context

Current CSV loading in the codebase has mixed responsibilities:
- `load_csvs` loads CSV files but also transforms single price columns to OHLC format
- `load_price_df` handles OHLC format loading with proper UTC timezone handling
- Test fixtures rely on the transformation logic in `load_csvs`

This creates confusion about which function to use for different CSV formats and leads to duplicated logic.

## Goals / Non-Goals

**Goals:**
- Clear separation of responsibilities: `load_csvs` only loads raw CSV data
- Single source of truth for OHLC format loading via `load_price_df`
- Consistent timezone handling across all CSV loading
- Simplified test fixture setup

**Non-Goals:**
- Changing the OHLC format specification
- Modifying existing CSV file formats
- Breaking existing `load_price_df` API

## Decisions

- **Keep `load_csvs` as simple CSV loader**: Remove transformation logic, only return raw DataFrames
- **Use `load_price_df` for OHLC files**: Direct usage for files with OHLC columns
- **Update test fixtures**: Remove manual OHLC transformation in conftest.py
- **Maintain backward compatibility**: Existing `load_price_df` API unchanged

## Risks / Trade-offs

- **Risk**: Existing code may depend on `load_csvs` transformation → **Mitigation**: Update all usages during implementation
- **Trade-off**: More explicit function calls needed → **Benefit**: Clearer intent and better separation of concerns

## Migration Plan

1. Refactor `load_csvs` to remove OHLC transformation logic
2. Update test fixtures in `conftest.py` to use `load_price_df` directly
3. Update any code that uses `load_csvs` for OHLC files
4. Run tests to ensure no regressions

## Open Questions

- Are there other files besides test fixtures that use `load_csvs` for OHLC data?
