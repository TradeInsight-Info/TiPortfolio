# Fix Example 20 Date Range & Simplify Data Normalization

**Goal**: Allow each portfolio in example 20 to use its own natural date range (QQQ from Jan 2025, ALLW from Mar 2025) and simplify duplicated data normalization code.
**Architecture**: Backtest engine already subsets data per portfolio via `_leaf_ticker_names()`. The example just needs to fetch with a wider date range. The data layer has duplicated normalization logic to consolidate.
**Tech Stack**: Python 3.12, pandas, yfinance
**Spec**: `openspec/changes/fix-example20-date-range/specs/`

## File Map:

1. Modify : `examples/20_fetch_and_hold.py` - Change start date to Jan 2025 so QQQ gets full year of data; update docstring
2. Modify : `src/tiportfolio/data.py` - Extract shared `_normalize_ticker_df()` from `_load_from_csv` and `_split_flat_to_dict`
3. Modify : `tests/test_data.py` - Verify normalization helper works correctly (existing tests should cover)

## Chunks

### Chunk 1: Fix example 20 date range
Update example to use a wider date range so QQQ starts from Jan 2025 while ALLW naturally starts from Mar 2025 (via the existing `dropna(how="all")` in `_split_flat_to_dict`). The `Backtest` constructor already subsets data per portfolio, so this just works.

Files:
- `examples/20_fetch_and_hold.py`
Steps:
- Step 1: Change `start="2025-03-05"` to `start="2025-01-02"` (first trading day of 2025)
- Step 2: Update docstring to reflect the new date range
- Step 3: Verify chart shows QQQ from Jan and ALLW from Mar

### Chunk 2: Simplify data normalization
Both `_load_from_csv` and `_split_flat_to_dict` duplicate the same pattern: lowercase columns → timezone normalize → sort index. Extract a shared helper to eliminate duplication.

Files:
- `src/tiportfolio/data.py`
Steps:
- Step 1: Extract `_normalize_ticker_df(df, default_tz)` helper that handles: lowercase columns, tz localize/convert to UTC, sort_index, dropna
- Step 2: Refactor `_load_from_csv` to use the helper (default_tz="UTC")
- Step 3: Refactor `_split_flat_to_dict` to use the helper (default_tz="US/Eastern")
- Step 4: Run existing tests to verify no regression
